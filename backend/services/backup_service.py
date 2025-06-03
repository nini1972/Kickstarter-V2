"""
💾 Production Backup Service
Automated backup and disaster recovery for MongoDB Atlas
"""

import asyncio
import logging
import os
import json
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
from motor.motor_asyncio import AsyncIOMotorClient
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BackupService:
    """
    Comprehensive backup service for production data protection
    """
    
    def __init__(self, database=None):
        self.database = database
        self.backup_config = {
            "retention_days": int(os.environ.get('BACKUP_RETENTION_DAYS', '30')),
            "compression": os.environ.get('BACKUP_COMPRESSION', 'true').lower() == 'true',
            "encryption": os.environ.get('BACKUP_ENCRYPTION', 'true').lower() == 'true',
            "local_path": os.environ.get('BACKUP_LOCAL_PATH', '/tmp/backups'),
            "s3_bucket": os.environ.get('BACKUP_S3_BUCKET'),
            "s3_region": os.environ.get('BACKUP_S3_REGION', 'us-east-1')
        }
        
        # Create backup directory
        Path(self.backup_config["local_path"]).mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.backup_config["s3_bucket"]:
            try:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.backup_config["s3_region"],
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                )
            except Exception as e:
                logger.warning(f"S3 backup not configured: {e}")
    
    async def create_full_backup(self) -> Dict[str, Any]:
        """
        Create a full database backup
        
        Returns:
            Backup creation result with metadata
        """
        backup_id = f"full_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        logger.info(f"🔄 Starting full backup: {backup_id}")
        
        try:
            backup_data = {}
            total_documents = 0
            
            # Get all collections
            collection_names = await self.database.list_collection_names()
            
            # Backup each collection
            for collection_name in collection_names:
                if collection_name.startswith('system.'):
                    continue  # Skip system collections
                
                logger.info(f"📦 Backing up collection: {collection_name}")
                
                collection = self.database.get_collection(collection_name)
                documents = []
                
                # Stream documents to handle large collections
                async for document in collection.find():
                    # Convert ObjectId and other non-JSON types to strings
                    document = self._serialize_document(document)
                    documents.append(document)
                
                backup_data[collection_name] = documents
                total_documents += len(documents)
                
                logger.info(f"✅ Backed up {len(documents)} documents from {collection_name}")
            
            # Create backup metadata
            backup_metadata = {
                "backup_id": backup_id,
                "type": "full_backup",
                "timestamp": start_time.isoformat(),
                "collections": list(backup_data.keys()),
                "total_documents": total_documents,
                "version": "1.0"
            }
            
            # Save backup to file
            backup_file_path = await self._save_backup_to_file(backup_id, backup_data, backup_metadata)
            
            # Upload to S3 if configured
            s3_location = None
            if self.s3_client:
                s3_location = await self._upload_backup_to_s3(backup_file_path, backup_id)
            
            # Calculate backup duration
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Update metadata with results
            backup_result = {
                "backup_id": backup_id,
                "status": "success",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration_seconds,
                "total_documents": total_documents,
                "collections_backed_up": len(backup_data),
                "local_file_path": str(backup_file_path),
                "s3_location": s3_location,
                "file_size_bytes": backup_file_path.stat().st_size if backup_file_path.exists() else 0
            }
            
            # Store backup metadata in database
            await self._store_backup_metadata(backup_result)
            
            logger.info(f"✅ Full backup completed: {backup_id} ({duration_seconds:.2f}s)")
            return backup_result
            
        except Exception as e:
            logger.error(f"❌ Full backup failed: {e}")
            
            error_result = {
                "backup_id": backup_id,
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            
            await self._store_backup_metadata(error_result)
            return error_result
    
    async def create_incremental_backup(self, since: datetime) -> Dict[str, Any]:
        """
        Create an incremental backup since specified timestamp
        
        Args:
            since: Timestamp to backup changes since
            
        Returns:
            Incremental backup result
        """
        backup_id = f"incremental_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        logger.info(f"🔄 Starting incremental backup: {backup_id} (since {since})")
        
        try:
            backup_data = {}
            total_documents = 0
            
            # Get collections with timestamp tracking
            trackable_collections = ["projects", "investments", "users", "analytics_cache"]
            
            for collection_name in trackable_collections:
                try:
                    collection = self.database.get_collection(collection_name)
                    
                    # Find documents modified since last backup
                    query = {
                        "$or": [
                            {"created_at": {"$gte": since}},
                            {"updated_at": {"$gte": since}}
                        ]
                    }
                    
                    documents = []
                    async for document in collection.find(query):
                        document = self._serialize_document(document)
                        documents.append(document)
                    
                    if documents:
                        backup_data[collection_name] = documents
                        total_documents += len(documents)
                        logger.info(f"📦 Incremental backup: {len(documents)} documents from {collection_name}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to backup collection {collection_name}: {e}")
                    continue
            
            # Create backup metadata
            backup_metadata = {
                "backup_id": backup_id,
                "type": "incremental_backup",
                "timestamp": start_time.isoformat(),
                "since_timestamp": since.isoformat(),
                "collections": list(backup_data.keys()),
                "total_documents": total_documents,
                "version": "1.0"
            }
            
            # Save backup to file
            backup_file_path = await self._save_backup_to_file(backup_id, backup_data, backup_metadata)
            
            # Upload to S3 if configured
            s3_location = None
            if self.s3_client and total_documents > 0:
                s3_location = await self._upload_backup_to_s3(backup_file_path, backup_id)
            
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            
            backup_result = {
                "backup_id": backup_id,
                "status": "success",
                "type": "incremental",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration_seconds,
                "since_timestamp": since.isoformat(),
                "total_documents": total_documents,
                "collections_backed_up": len(backup_data),
                "local_file_path": str(backup_file_path),
                "s3_location": s3_location,
                "file_size_bytes": backup_file_path.stat().st_size if backup_file_path.exists() else 0
            }
            
            await self._store_backup_metadata(backup_result)
            
            logger.info(f"✅ Incremental backup completed: {backup_id} ({total_documents} docs, {duration_seconds:.2f}s)")
            return backup_result
            
        except Exception as e:
            logger.error(f"❌ Incremental backup failed: {e}")
            
            error_result = {
                "backup_id": backup_id,
                "status": "failed",
                "type": "incremental",
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            
            await self._store_backup_metadata(error_result)
            return error_result
    
    def _serialize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize MongoDB document for JSON backup
        
        Args:
            document: MongoDB document
            
        Returns:
            JSON-serializable document
        """
        from bson import ObjectId
        
        def serialize_value(value):
            if isinstance(value, ObjectId):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                return value
        
        return {key: serialize_value(value) for key, value in document.items()}
    
    async def _save_backup_to_file(self, backup_id: str, backup_data: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> Path:
        """
        Save backup data to local file with compression
        
        Args:
            backup_id: Unique backup identifier
            backup_data: Backup data to save
            metadata: Backup metadata
            
        Returns:
            Path to saved backup file
        """
        filename = f"{backup_id}.json"
        if self.backup_config["compression"]:
            filename += ".gz"
        
        file_path = Path(self.backup_config["local_path"]) / filename
        
        # Combine metadata and data
        full_backup = {
            "metadata": metadata,
            "data": backup_data
        }
        
        backup_json = json.dumps(full_backup, indent=2, default=str)
        
        if self.backup_config["compression"]:
            # Compress backup
            async with aiofiles.open(file_path, 'wb') as f:
                compressed_data = gzip.compress(backup_json.encode('utf-8'))
                await f.write(compressed_data)
        else:
            # Save uncompressed
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(backup_json)
        
        logger.info(f"💾 Backup saved to: {file_path}")
        return file_path
    
    async def _upload_backup_to_s3(self, file_path: Path, backup_id: str) -> Optional[str]:
        """
        Upload backup file to S3
        
        Args:
            file_path: Local file path
            backup_id: Backup identifier
            
        Returns:
            S3 location URL or None if failed
        """
        if not self.s3_client:
            return None
        
        try:
            s3_key = f"backups/{datetime.utcnow().strftime('%Y/%m/%d')}/{backup_id}/{file_path.name}"
            
            # Upload file
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.upload_file,
                str(file_path),
                self.backup_config["s3_bucket"],
                s3_key
            )
            
            s3_location = f"s3://{self.backup_config['s3_bucket']}/{s3_key}"
            logger.info(f"☁️ Backup uploaded to S3: {s3_location}")
            
            return s3_location
            
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return None
    
    async def _store_backup_metadata(self, backup_result: Dict[str, Any]) -> None:
        """
        Store backup metadata in database
        
        Args:
            backup_result: Backup result metadata
        """
        try:
            if self.database:
                backups_collection = self.database.get_collection("backup_metadata")
                
                # Add TTL for automatic cleanup
                backup_result["expires_at"] = datetime.utcnow() + timedelta(
                    days=self.backup_config["retention_days"]
                )
                
                await backups_collection.insert_one(backup_result)
                
                logger.info(f"📝 Backup metadata stored: {backup_result['backup_id']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to store backup metadata: {e}")
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Clean up old backup files based on retention policy
        
        Returns:
            Cleanup result summary
        """
        logger.info("🧹 Starting backup cleanup...")
        
        cleanup_result = {
            "start_time": datetime.utcnow().isoformat(),
            "local_files_deleted": 0,
            "s3_objects_deleted": 0,
            "errors": []
        }
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.backup_config["retention_days"])
            
            # Clean up local files
            backup_dir = Path(self.backup_config["local_path"])
            for backup_file in backup_dir.glob("*.json*"):
                try:
                    file_stat = backup_file.stat()
                    file_date = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        cleanup_result["local_files_deleted"] += 1
                        logger.info(f"🗑️ Deleted old backup file: {backup_file.name}")
                        
                except Exception as e:
                    cleanup_result["errors"].append(f"Failed to delete {backup_file}: {str(e)}")
            
            # Clean up S3 objects if configured
            if self.s3_client:
                s3_cleanup_result = await self._cleanup_s3_backups(cutoff_date)
                cleanup_result["s3_objects_deleted"] = s3_cleanup_result["deleted_count"]
                cleanup_result["errors"].extend(s3_cleanup_result["errors"])
            
            cleanup_result["end_time"] = datetime.utcnow().isoformat()
            cleanup_result["status"] = "success"
            
            logger.info(f"✅ Backup cleanup completed: {cleanup_result['local_files_deleted']} local, {cleanup_result['s3_objects_deleted']} S3")
            
        except Exception as e:
            cleanup_result["status"] = "failed"
            cleanup_result["error"] = str(e)
            cleanup_result["end_time"] = datetime.utcnow().isoformat()
            logger.error(f"❌ Backup cleanup failed: {e}")
        
        return cleanup_result
    
    async def _cleanup_s3_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """
        Clean up old S3 backup objects
        
        Args:
            cutoff_date: Delete objects older than this date
            
        Returns:
            S3 cleanup result
        """
        result = {"deleted_count": 0, "errors": []}
        
        try:
            # List objects in backup prefix
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.list_objects_v2,
                {"Bucket": self.backup_config["s3_bucket"], "Prefix": "backups/"}
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        try:
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.s3_client.delete_object,
                                {"Bucket": self.backup_config["s3_bucket"], "Key": obj['Key']}
                            )
                            result["deleted_count"] += 1
                            logger.info(f"🗑️ Deleted old S3 backup: {obj['Key']}")
                            
                        except Exception as e:
                            result["errors"].append(f"Failed to delete S3 object {obj['Key']}: {str(e)}")
            
        except Exception as e:
            result["errors"].append(f"S3 cleanup failed: {str(e)}")
        
        return result
    
    async def get_backup_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get backup history from metadata
        
        Args:
            limit: Maximum number of backup records to return
            
        Returns:
            List of backup metadata records
        """
        try:
            if not self.database:
                return []
            
            backups_collection = self.database.get_collection("backup_metadata")
            
            cursor = backups_collection.find(
                {},
                {"_id": 0}
            ).sort("start_time", -1).limit(limit)
            
            history = await cursor.to_list(length=limit)
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get backup history: {e}")
            return []

# Global backup service instance
backup_service = BackupService()
