"""
🚨 Alert Service
Intelligent notification and recommendation system with priority management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import hashlib

from models.projects import KickstarterProject
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class AlertService:
    """Service for managing intelligent alerts and notifications"""
    
    def __init__(self, database):
        self.db = database
        self.projects_collection = database.projects
        self.investments_collection = database.investments
        self.alert_settings_collection = database.alert_settings
        self.user_alerts_collection = database.user_alerts
    
    async def generate_smart_alerts(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Generate intelligent alerts based on project analysis and user preferences"""
        try:
            # Check cache first
            cache_key = f"smart_alerts_{user_id or 'global'}_{limit}"
            cached_alerts = await cache_service.get(cache_key)
            if cached_alerts:
                return cached_alerts
            
            logger.info("🚨 Generating smart alerts...")
            
            # Get relevant projects
            query = {"user_id": user_id} if user_id else {}
            projects_cursor = self.projects_collection.find(query)
            projects_data = await projects_cursor.to_list(length=None)
            
            if not projects_data:
                return []
            
            alerts = []
            current_time = datetime.utcnow()
            
            for project_data in projects_data:
                try:
                    project = KickstarterProject(**project_data)
                    project_alerts = await self._analyze_project_for_alerts(project, current_time)
                    alerts.extend(project_alerts)
                    
                except Exception as e:
                    logger.error(f"Error analyzing project {project_data.get('id')}: {e}")
                    continue
            
            # Sort alerts by priority and score
            alerts.sort(key=lambda x: (
                self._get_priority_weight(x["priority"]), 
                x["alert_score"]
            ), reverse=True)
            
            # Limit results
            final_alerts = alerts[:limit]
            
            # Cache for 10 minutes
            await cache_service.set(cache_key, final_alerts, 600)
            
            logger.info(f"✅ Generated {len(final_alerts)} smart alerts")
            return final_alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to generate smart alerts: {e}")
            return []
    
    async def _analyze_project_for_alerts(self, project: KickstarterProject, current_time: datetime) -> List[Dict[str, Any]]:
        """Analyze a single project for alert opportunities"""
        alerts = []
        
        try:
            # Calculate project metrics
            funding_percentage = project.funding_percentage()
            days_remaining = project.days_remaining()
            ai_analysis = project.ai_analysis or {}
            success_probability = ai_analysis.get("success_probability", 50)
            risk_level = ai_analysis.get("risk_level", "medium")
            
            # Alert scoring system
            alert_score = 0
            alert_reasons = []
            alert_type = "opportunity"
            priority = "LOW"
            
            # 1. Funding Momentum Analysis (High Priority)
            if funding_percentage > 90 and days_remaining > 3:
                alert_score += 35
                alert_reasons.append("🔥 Strong funding momentum with time remaining")
                priority = "HIGH"
                alert_type = "funding_momentum"
            elif funding_percentage > 75 and days_remaining > 5:
                alert_score += 25
                alert_reasons.append("📈 Good funding progress")
                priority = "MEDIUM"
            
            # 2. Success Probability Assessment (High Priority)
            if success_probability > 85:
                alert_score += 30
                alert_reasons.append(f"🎯 Very high success probability ({success_probability}%)")
                priority = max(priority, "HIGH", key=self._get_priority_weight)
            elif success_probability > 70:
                alert_score += 20
                alert_reasons.append(f"✅ Good success probability ({success_probability}%)")
                priority = max(priority, "MEDIUM", key=self._get_priority_weight)
            
            # 3. Risk Assessment (Medium Priority)
            if risk_level == "low" and success_probability > 60:
                alert_score += 25
                alert_reasons.append("🛡️ Low risk with good potential")
            elif risk_level == "medium" and success_probability > 75:
                alert_score += 15
                alert_reasons.append("⚖️ Balanced risk with high potential")
            
            # 4. Deadline Urgency (High Priority)
            if days_remaining <= 3 and funding_percentage >= 50:
                alert_score += 30
                alert_reasons.append(f"🚨 URGENT: Only {days_remaining} days left!")
                priority = "CRITICAL"
                alert_type = "deadline_critical"
            elif days_remaining <= 7 and funding_percentage >= 60:
                alert_score += 20
                alert_reasons.append(f"⏰ Final week with {funding_percentage:.1f}% funded")
                priority = max(priority, "HIGH", key=self._get_priority_weight)
            
            # 5. Category Performance (Low Priority)
            high_performing_categories = ["Technology", "Design", "Games", "Innovation"]
            if project.category in high_performing_categories:
                alert_score += 8
                alert_reasons.append(f"🏆 Strong category: {project.category}")
            
            # 6. AI Recommendation Alignment (Medium Priority)
            recommendation = ai_analysis.get("recommendation", "hold")
            if recommendation in ["strong_buy", "buy"]:
                alert_score += 15
                alert_reasons.append(f"🤖 AI recommends: {recommendation.replace('_', ' ').title()}")
            
            # 7. Funding Pattern Analysis (Medium Priority)
            if funding_percentage > 100:
                alert_score += 20
                alert_reasons.append("🎉 Successfully funded - potential overfunding opportunity")
                alert_type = "overfunded"
            elif funding_percentage < 25 and days_remaining <= 10:
                alert_score -= 15
                alert_reasons.append("⚠️ Low funding with approaching deadline")
                alert_type = "struggling"
                priority = "LOW"
            
            # 8. ROI Potential (Medium Priority)
            roi_potential = ai_analysis.get("roi_potential", "moderate")
            if roi_potential in ["excellent", "good"]:
                alert_score += 12
                alert_reasons.append(f"💰 {roi_potential.title()} ROI potential")
            
            # Generate alert if score meets threshold
            if alert_score >= 20:  # Minimum threshold
                
                alert = {
                    "id": str(uuid.uuid4())[:8],
                    "project_id": project.id,
                    "project_name": project.name,
                    "category": project.category,
                    "alert_type": alert_type,
                    "priority": priority,
                    "priority_emoji": self._get_priority_emoji(priority),
                    "alert_score": alert_score,
                    "title": self._generate_alert_title(priority, alert_type, project.name),
                    "message": self._generate_alert_message(project, alert_type, funding_percentage, days_remaining),
                    "reasons": alert_reasons,
                    "metrics": {
                        "funding_percentage": round(funding_percentage, 1),
                        "days_remaining": days_remaining,
                        "success_probability": success_probability,
                        "risk_level": risk_level,
                        "goal_amount": project.goal_amount,
                        "pledged_amount": project.pledged_amount,
                        "backers_count": project.backers_count
                    },
                    "created_at": current_time.isoformat(),
                    "expires_at": (current_time + timedelta(hours=24)).isoformat(),
                    "action_items": self._generate_action_items(project, alert_score, alert_type),
                    "confidence_level": self._calculate_confidence_level(ai_analysis, funding_percentage),
                    "investment_recommendation": self._generate_investment_recommendation(
                        alert_score, risk_level, success_probability, funding_percentage
                    )
                }
                
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error analyzing project {project.id} for alerts: {e}")
        
        return alerts
    
    async def get_user_alert_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's alert preferences"""
        try:
            preferences = await self.alert_settings_collection.find_one({"user_id": user_id})
            
            if not preferences:
                # Return default preferences
                return {
                    "user_id": user_id,
                    "enabled": True,
                    "min_alert_score": 25,
                    "priority_filter": ["CRITICAL", "HIGH", "MEDIUM"],
                    "alert_types": ["opportunity", "deadline_critical", "funding_momentum", "overfunded"],
                    "categories": [],  # Empty means all categories
                    "max_alerts_per_day": 10,
                    "email_notifications": False,
                    "push_notifications": True,
                    "quiet_hours": {"enabled": False, "start": "22:00", "end": "08:00"}
                }
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get alert preferences for user {user_id}: {e}")
            return {"user_id": user_id, "enabled": False}
    
    async def update_user_alert_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user's alert preferences"""
        try:
            preferences["user_id"] = user_id
            preferences["updated_at"] = datetime.utcnow()
            
            result = await self.alert_settings_collection.update_one(
                {"user_id": user_id},
                {"$set": preferences},
                upsert=True
            )
            
            # Invalidate alert cache for this user
            await cache_service.delete_pattern(f"smart_alerts_{user_id}_*")
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to update alert preferences for user {user_id}: {e}")
            return False
    
    async def mark_alert_as_read(self, alert_id: str, user_id: str) -> bool:
        """Mark an alert as read"""
        try:
            result = await self.user_alerts_collection.update_one(
                {"alert_id": alert_id, "user_id": user_id},
                {"$set": {"read_at": datetime.utcnow(), "is_read": True}},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to mark alert {alert_id} as read: {e}")
            return False
    
    async def get_alert_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics about alert generation and effectiveness"""
        try:
            # This would typically track alert performance over time
            # For now, we'll return basic metrics
            
            alerts = await self.generate_smart_alerts(user_id, limit=100)
            
            if not alerts:
                return {
                    "total_alerts": 0,
                    "priority_distribution": {},
                    "type_distribution": {},
                    "average_score": 0,
                    "effectiveness_score": 0
                }
            
            # Calculate distributions
            priority_dist = {}
            type_dist = {}
            total_score = 0
            
            for alert in alerts:
                priority = alert["priority"]
                alert_type = alert["alert_type"]
                score = alert["alert_score"]
                
                priority_dist[priority] = priority_dist.get(priority, 0) + 1
                type_dist[alert_type] = type_dist.get(alert_type, 0) + 1
                total_score += score
            
            return {
                "total_alerts": len(alerts),
                "priority_distribution": priority_dist,
                "type_distribution": type_dist,
                "average_score": total_score / len(alerts) if alerts else 0,
                "effectiveness_score": min((total_score / len(alerts)) * 1.5, 100) if alerts else 0,
                "last_generated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert analytics: {e}")
            return {}
    
    # Helper methods
    
    def _get_priority_weight(self, priority: str) -> int:
        """Get numeric weight for priority sorting"""
        weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return weights.get(priority, 1)
    
    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji for priority level"""
        emojis = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        return emojis.get(priority, "🟢")
    
    def _generate_alert_title(self, priority: str, alert_type: str, project_name: str) -> str:
        """Generate alert title based on priority and type"""
        emoji = self._get_priority_emoji(priority)
        
        titles = {
            "opportunity": f"{emoji} Investment Opportunity",
            "deadline_critical": f"{emoji} URGENT: Deadline Approaching",
            "funding_momentum": f"{emoji} Strong Funding Momentum",
            "overfunded": f"{emoji} Overfunding Success",
            "struggling": f"{emoji} Project at Risk"
        }
        
        base_title = titles.get(alert_type, f"{emoji} Project Alert")
        return f"{base_title}: {project_name}"
    
    def _generate_alert_message(self, project: KickstarterProject, alert_type: str, funding_pct: float, days_remaining: int) -> str:
        """Generate contextual alert message"""
        messages = {
            "opportunity": f"Project shows strong investment potential with {funding_pct:.1f}% funding and {days_remaining} days remaining.",
            "deadline_critical": f"URGENT: Only {days_remaining} days left! Currently at {funding_pct:.1f}% funding.",
            "funding_momentum": f"Excellent momentum with {funding_pct:.1f}% funding achieved and {days_remaining} days remaining.",
            "overfunded": f"Successfully funded at {funding_pct:.1f}%! Consider the potential for additional rewards.",
            "struggling": f"Project needs support - only {funding_pct:.1f}% funded with {days_remaining} days left."
        }
        
        return messages.get(alert_type, f"Project update: {funding_pct:.1f}% funded, {days_remaining} days remaining.")
    
    def _generate_action_items(self, project: KickstarterProject, alert_score: int, alert_type: str) -> List[str]:
        """Generate actionable recommendations"""
        actions = []
        
        funding_pct = project.funding_percentage()
        days_remaining = project.days_remaining()
        
        if alert_type == "deadline_critical":
            actions.append("🚨 Immediate action required - deadline approaching")
            actions.append("📊 Review final project metrics")
        elif alert_type == "opportunity":
            actions.append("🎯 Evaluate investment opportunity")
            actions.append("📋 Review project details and creator track record")
        elif alert_type == "funding_momentum":
            actions.append("⚡ Consider investing while momentum is strong")
            actions.append("📈 Monitor continued funding progress")
        
        if alert_score >= 50:
            actions.append("🔍 Conduct detailed due diligence")
            actions.append("💼 Assess portfolio fit and risk tolerance")
        
        if funding_pct > 90:
            actions.append("🎉 Review stretch goals and additional rewards")
        
        if days_remaining <= 7:
            actions.append("⏰ Time-sensitive opportunity")
        
        # Always include these
        actions.append("🤖 Review AI analysis and recommendations")
        actions.append("📱 Set up project monitoring")
        
        return actions[:6]  # Limit to 6 actions
    
    def _calculate_confidence_level(self, ai_analysis: Dict[str, Any], funding_percentage: float) -> str:
        """Calculate confidence level for the alert"""
        confidence_score = 0
        
        # AI analysis confidence
        success_prob = ai_analysis.get("success_probability", 0)
        if success_prob > 80:
            confidence_score += 35
        elif success_prob > 60:
            confidence_score += 25
        elif success_prob > 40:
            confidence_score += 15
        
        # Funding trajectory confidence
        if funding_percentage > 90:
            confidence_score += 30
        elif funding_percentage > 75:
            confidence_score += 25
        elif funding_percentage > 50:
            confidence_score += 15
        elif funding_percentage > 25:
            confidence_score += 10
        
        # Risk level confidence
        risk_level = ai_analysis.get("risk_level", "medium")
        if risk_level == "low":
            confidence_score += 20
        elif risk_level == "medium":
            confidence_score += 10
        
        # AI recommendation confidence
        recommendation = ai_analysis.get("recommendation", "hold")
        if recommendation == "strong_buy":
            confidence_score += 15
        elif recommendation == "buy":
            confidence_score += 10
        
        if confidence_score >= 70:
            return "HIGH"
        elif confidence_score >= 45:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_investment_recommendation(self, alert_score: int, risk_level: str, success_prob: int, funding_pct: float) -> Dict[str, Any]:
        """Generate specific investment recommendation"""
        
        # Base recommendation
        if alert_score >= 60 and success_prob > 75 and risk_level in ["low", "medium"]:
            action = "STRONG_BUY"
            reasoning = "High alert score with low risk and good success probability"
        elif alert_score >= 40 and success_prob > 60:
            action = "BUY"
            reasoning = "Good opportunity with acceptable risk levels"
        elif alert_score >= 25 and success_prob > 40:
            action = "CONSIDER"
            reasoning = "Moderate opportunity - conduct further research"
        else:
            action = "HOLD"
            reasoning = "Insufficient signals for investment recommendation"
        
        # Suggested investment amount (as percentage of typical investment)
        if action == "STRONG_BUY":
            suggested_amount_pct = "15-25%"
        elif action == "BUY":
            suggested_amount_pct = "10-15%"
        elif action == "CONSIDER":
            suggested_amount_pct = "5-10%"
        else:
            suggested_amount_pct = "0%"
        
        return {
            "action": action,
            "reasoning": reasoning,
            "suggested_amount_percentage": suggested_amount_pct,
            "urgency": "HIGH" if funding_pct > 80 else "MEDIUM" if funding_pct > 50 else "LOW"
        }

# Global alert service instance will be initialized with database
alert_service = None

def initialize_alert_service(database):
    """Initialize alert service with database connection"""
    global alert_service
    alert_service = AlertService(database)
    return alert_service