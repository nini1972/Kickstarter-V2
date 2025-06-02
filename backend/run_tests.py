#!/usr/bin/env python3
"""
🧪 Comprehensive Test Runner
Enterprise-grade test execution with detailed reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import json


class TestRunner:
    """Comprehensive test runner with advanced reporting"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_unit_tests(self, verbose=False):
        """Run unit tests with coverage"""
        print("🔬 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "-v" if verbose else "",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--junit-xml=reports/unit-tests.xml",
            "--html=reports/unit-tests.html",
            "--self-contained-html",
            "-m", "unit"
        ]
        
        return self._run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v" if verbose else "",
            "--junit-xml=reports/integration-tests.xml",
            "--html=reports/integration-tests.html",
            "--self-contained-html",
            "-m", "integration"
        ]
        
        return self._run_command(cmd, "Integration Tests")
    
    def run_security_tests(self, verbose=False):
        """Run security-specific tests"""
        print("🛡️ Running Security Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v" if verbose else "",
            "--junit-xml=reports/security-tests.xml",
            "--html=reports/security-tests.html",
            "--self-contained-html",
            "-m", "security"
        ]
        
        return self._run_command(cmd, "Security Tests")
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests"""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v" if verbose else "",
            "--benchmark-only",
            "--benchmark-json=reports/benchmark.json",
            "--junit-xml=reports/performance-tests.xml",
            "--html=reports/performance-tests.html",
            "--self-contained-html",
            "-m", "performance"
        ]
        
        return self._run_command(cmd, "Performance Tests")
    
    def run_all_tests(self, verbose=False):
        """Run all test suites"""
        print("🧪 Running Complete Test Suite...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v" if verbose else "",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--junit-xml=reports/all-tests.xml",
            "--html=reports/all-tests.html",
            "--self-contained-html",
            "--benchmark-json=reports/benchmark.json"
        ]
        
        return self._run_command(cmd, "All Tests")
    
    def run_quick_tests(self, verbose=False):
        """Run quick subset of tests for development"""
        print("🚀 Running Quick Test Suite...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/test_models.py",
            "tests/integration/test_api_endpoints.py::TestAuthenticationEndpoints::test_demo_login_success",
            "-v" if verbose else "",
            "--tb=short"
        ]
        
        return self._run_command(cmd, "Quick Tests")
    
    def _run_command(self, cmd, test_type):
        """Execute test command and handle results"""
        # Filter empty strings from command
        cmd = [c for c in cmd if c]
        
        try:
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {test_type} PASSED")
                if result.stdout:
                    print(result.stdout[-500:])  # Last 500 chars
            else:
                print(f"❌ {test_type} FAILED (exit code: {result.returncode})")
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])
                if result.stdout:
                    print("STDOUT:", result.stdout[-500:])
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_type} TIMED OUT")
            return False
        except Exception as e:
            print(f"💥 {test_type} ERROR: {e}")
            return False
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("📊 Generating Coverage Report...")
        
        try:
            # Generate coverage report
            subprocess.run([
                "python", "-m", "coverage", "report", "--format=markdown"
            ], cwd=self.test_dir)
            
            # Generate HTML report
            subprocess.run([
                "python", "-m", "coverage", "html"
            ], cwd=self.test_dir)
            
            print("✅ Coverage report generated in htmlcov/")
            
        except Exception as e:
            print(f"❌ Coverage report failed: {e}")
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("📋 Generating Test Summary...")
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suites": {},
            "overall_status": "unknown"
        }
        
        # Check for test result files
        report_files = {
            "unit": self.reports_dir / "unit-tests.xml",
            "integration": self.reports_dir / "integration-tests.xml",
            "security": self.reports_dir / "security-tests.xml",
            "performance": self.reports_dir / "performance-tests.xml",
            "all": self.reports_dir / "all-tests.xml"
        }
        
        for suite_name, report_file in report_files.items():
            if report_file.exists():
                summary["test_suites"][suite_name] = {
                    "report_file": str(report_file),
                    "status": "completed"
                }
            else:
                summary["test_suites"][suite_name] = {
                    "status": "not_run"
                }
        
        # Save summary
        summary_file = self.reports_dir / "test-summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Test summary saved to {summary_file}")
        return summary
    
    def check_dependencies(self):
        """Check if all test dependencies are available"""
        print("🔍 Checking Test Dependencies...")
        
        required_packages = [
            "pytest", "pytest-asyncio", "pytest-cov", "pytest-mock",
            "pytest-benchmark", "pytest-html", "httpx", "faker"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All dependencies available")
        return True


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--suite", choices=["unit", "integration", "security", "performance", "all", "quick"], 
                       default="quick", help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--summary", action="store_true", help="Generate test summary")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Check dependencies
    if args.check_deps:
        return 0 if runner.check_dependencies() else 1
    
    if not runner.check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Run tests
    success = True
    
    if args.suite == "unit":
        success = runner.run_unit_tests(args.verbose)
    elif args.suite == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.suite == "security":
        success = runner.run_security_tests(args.verbose)
    elif args.suite == "performance":
        success = runner.run_performance_tests(args.verbose)
    elif args.suite == "all":
        success = runner.run_all_tests(args.verbose)
    elif args.suite == "quick":
        success = runner.run_quick_tests(args.verbose)
    
    # Generate reports if requested
    if args.coverage:
        runner.generate_coverage_report()
    
    if args.summary:
        runner.generate_test_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
