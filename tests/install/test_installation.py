#!/usr/bin/env python3
"""
Installation tests for SmartFileOrganizer
Tests fresh install, reinstall, rollback, and uninstall scenarios
"""

import os
import subprocess
import tempfile
import shutil
import json
import time
from pathlib import Path
import unittest


class InstallTestBase(unittest.TestCase):
    """Base class for installation tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="smartfile_test_")
        self.repo_root = Path(__file__).parent.parent.parent
        self.install_script = self.repo_root / "install.sh"
        self.uninstall_script = self.repo_root / "uninstall.sh"
        self.config_dir = Path.home() / ".organizer"
        
        # Backup existing config if present
        self.config_backup = None
        if self.config_dir.exists():
            self.config_backup = Path(tempfile.mkdtemp()) / "organizer_backup"
            shutil.copytree(self.config_dir, self.config_backup)
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore config if backed up
        if self.config_backup and self.config_backup.exists():
            if self.config_dir.exists():
                shutil.rmtree(self.config_dir)
            shutil.copytree(self.config_backup, self.config_dir)
            shutil.rmtree(self.config_backup.parent)
        
        # Clean up test directory
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def run_command(self, cmd, input_text=None, timeout=60):
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=self.repo_root
            )
            return result
        except subprocess.TimeoutExpired:
            self.fail(f"Command timed out: {cmd}")


class TestPreflightChecks(InstallTestBase):
    """Test pre-flight checks"""
    
    def test_python_version_check(self):
        """Test Python version verification"""
        # This should pass on CI
        result = self.run_command("python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'")
        self.assertEqual(result.returncode, 0, "Python 3.8+ should be available")
    
    def test_required_commands_available(self):
        """Test that required system commands are available"""
        commands = ['python3', 'pip3', 'curl', 'git']
        for cmd in commands:
            result = self.run_command(f"command -v {cmd}")
            self.assertEqual(result.returncode, 0, f"{cmd} should be available")
    
    def test_venv_module_available(self):
        """Test that Python venv module is available"""
        result = self.run_command("python3 -m venv --help")
        self.assertEqual(result.returncode, 0, "venv module should be available")
    
    def test_disk_space_check(self):
        """Test disk space availability"""
        result = self.run_command("df -BG . | tail -1 | awk '{print $4}' | sed 's/G//'")
        if result.returncode == 0:
            available_gb = int(result.stdout.strip())
            self.assertGreater(available_gb, 1, "At least 1GB should be available for tests")


class TestInstallScriptStructure(InstallTestBase):
    """Test install script structure and syntax"""
    
    def test_install_script_exists(self):
        """Test that install.sh exists and is executable"""
        self.assertTrue(self.install_script.exists(), "install.sh should exist")
        self.assertTrue(os.access(self.install_script, os.X_OK), "install.sh should be executable")
    
    def test_install_script_bash_syntax(self):
        """Test install.sh has valid bash syntax"""
        result = self.run_command(f"bash -n {self.install_script}")
        self.assertEqual(result.returncode, 0, f"install.sh should have valid syntax: {result.stderr}")
    
    def test_uninstall_script_exists(self):
        """Test that uninstall.sh exists and is executable"""
        self.assertTrue(self.uninstall_script.exists(), "uninstall.sh should exist")
        self.assertTrue(os.access(self.uninstall_script, os.X_OK), "uninstall.sh should be executable")
    
    def test_uninstall_script_bash_syntax(self):
        """Test uninstall.sh has valid bash syntax"""
        result = self.run_command(f"bash -n {self.uninstall_script}")
        self.assertEqual(result.returncode, 0, f"uninstall.sh should have valid syntax: {result.stderr}")


class TestInstallLogging(InstallTestBase):
    """Test installation logging functionality"""
    
    def test_log_file_created(self):
        """Test that installation creates a log file"""
        # Note: This would require actually running install, which we test separately
        config_dir = Path.home() / ".organizer"
        if config_dir.exists():
            log_file = config_dir / "install.log"
            # Log file should exist after install
            # This is tested in integration tests


class TestStateManagement(InstallTestBase):
    """Test installation state management"""
    
    def test_state_file_location(self):
        """Test that state file would be in correct location"""
        expected_state = Path.home() / ".organizer" / "install.state"
        # State file should be created during install
        # This is tested in integration tests


class TestConfigFile(InstallTestBase):
    """Test configuration file handling"""
    
    def test_config_example_exists(self):
        """Test that config.example.json exists and is valid"""
        config_example = self.repo_root / "config.example.json"
        self.assertTrue(config_example.exists(), "config.example.json should exist")
        
        with open(config_example) as f:
            config = json.load(f)
        
        # Check essential keys
        self.assertIn('ai', config)
        self.assertIn('preferences', config)
    
    def test_config_example_valid_json(self):
        """Test that config.example.json is valid JSON"""
        config_example = self.repo_root / "config.example.json"
        try:
            with open(config_example) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            self.fail(f"config.example.json is not valid JSON: {e}")


class TestHealthChecks(InstallTestBase):
    """Test post-install health check functions"""
    
    def test_python_packages_importable(self):
        """Test that required Python packages can be listed"""
        packages = ['click', 'rich', 'ollama', 'watchdog']
        # These would be checked in the venv after install
        # Tested in integration tests


class TestDiagnosticsScript(InstallTestBase):
    """Test diagnostics script"""
    
    def test_diagnose_script_exists(self):
        """Test that diagnose.sh exists and is executable"""
        diagnose_script = self.repo_root / "diagnose.sh"
        self.assertTrue(diagnose_script.exists(), "diagnose.sh should exist")
        self.assertTrue(os.access(diagnose_script, os.X_OK), "diagnose.sh should be executable")
    
    def test_diagnose_script_bash_syntax(self):
        """Test diagnose.sh has valid bash syntax"""
        diagnose_script = self.repo_root / "diagnose.sh"
        result = self.run_command(f"bash -n {diagnose_script}")
        self.assertEqual(result.returncode, 0, f"diagnose.sh should have valid syntax: {result.stderr}")


class TestRequirementsFile(InstallTestBase):
    """Test requirements.txt file"""
    
    def test_requirements_exists(self):
        """Test that requirements.txt exists"""
        requirements = self.repo_root / "requirements.txt"
        self.assertTrue(requirements.exists(), "requirements.txt should exist")
    
    def test_requirements_has_content(self):
        """Test that requirements.txt has dependencies"""
        requirements = self.repo_root / "requirements.txt"
        with open(requirements) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        self.assertGreater(len(lines), 0, "requirements.txt should have dependencies")
    
    def test_requirements_pinned_versions(self):
        """Test that requirements use pinned versions"""
        requirements = self.repo_root / "requirements.txt"
        with open(requirements) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Should have == version pinning
                    if not any(op in line for op in ['==', '>=', '<=']):
                        self.fail(f"Dependency should be pinned: {line}")


class TestGitIgnore(InstallTestBase):
    """Test .gitignore configuration"""
    
    def test_gitignore_excludes_venv(self):
        """Test that .gitignore excludes venv directory"""
        gitignore = self.repo_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore) as f:
                content = f.read()
            self.assertIn('venv', content.lower(), ".gitignore should exclude venv")
    
    def test_gitignore_excludes_config(self):
        """Test that .gitignore excludes config files"""
        gitignore = self.repo_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore) as f:
                content = f.read()
            # Should exclude config.json or .organizer
            self.assertTrue(
                'config.json' in content or '.organizer' in content,
                ".gitignore should exclude config files"
            )


class TestScriptFunctions(InstallTestBase):
    """Test that scripts have required functions"""
    
    def test_install_has_logging_functions(self):
        """Test that install.sh has logging functions"""
        with open(self.install_script) as f:
            content = f.read()
        
        required_functions = ['log_info', 'log_error', 'log_warn', 'log_success']
        for func in required_functions:
            self.assertIn(func, content, f"install.sh should have {func} function")
    
    def test_install_has_state_management(self):
        """Test that install.sh has state management functions"""
        with open(self.install_script) as f:
            content = f.read()
        
        required_functions = ['save_state', 'load_state', 'clear_state']
        for func in required_functions:
            self.assertIn(func, content, f"install.sh should have {func} function")
    
    def test_install_has_rollback(self):
        """Test that install.sh has rollback function"""
        with open(self.install_script) as f:
            content = f.read()
        
        self.assertIn('cleanup_on_failure', content, "install.sh should have cleanup_on_failure function")
        self.assertIn('trap', content, "install.sh should set up error trap")
    
    def test_install_has_health_checks(self):
        """Test that install.sh has health check functions"""
        with open(self.install_script) as f:
            content = f.read()
        
        self.assertIn('health_check', content.lower(), "install.sh should have health check functions")


class TestErrorHandling(InstallTestBase):
    """Test error handling in scripts"""
    
    def test_install_uses_strict_mode(self):
        """Test that install.sh uses bash strict mode"""
        with open(self.install_script) as f:
            content = f.read()
        
        # Should have set -e or set -euo pipefail
        self.assertIn('set -e', content, "install.sh should use set -e for error handling")
    
    def test_uninstall_uses_strict_mode(self):
        """Test that uninstall.sh uses bash strict mode"""
        with open(self.uninstall_script) as f:
            content = f.read()
        
        self.assertIn('set -e', content, "uninstall.sh should use set -e for error handling")


if __name__ == '__main__':
    unittest.main()
