#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Main Orchestrator
Copyright (C) 2024 HOMESERVER LLC

Main orchestrator for ISO build process using recursive index pattern.
"""

import json
import os
import sys
from pathlib import Path
import re
# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import Colors


class Orchestrator:
    """Main orchestrator for ISO build process."""
    
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.config_path = index_path / 'index.json'
        self.config = self._load_config()
        self.paths = self._resolve_paths()
    
    def _load_config(self) -> dict:
        """Load configuration from index.json."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        return config
    
    def _resolve_paths(self) -> dict:
        """Resolve paths from config, expanding environment variables."""

        
        paths_config = self.config.get('paths', {})
        resolved = {}
        
        # Set default repo_root if not provided
        if 'repo_root' not in paths_config or not paths_config['repo_root']:
            # Default to parent of isoprep directory
            default_repo_root = Path(__file__).parent.parent.parent.resolve()
            os.environ['ISOPREP_REPO_ROOT'] = str(default_repo_root)
        
        def expand_bash_var(value: str) -> str:
            """Expand bash-style ${VAR:-default} syntax."""
            # Pattern to match ${VAR:-default}
            pattern = r'\$\{([^:}]+):-([^}]+)\}'
            def replacer(match):
                var_name = match.group(1)
                default = match.group(2)
                return os.environ.get(var_name, default)
            return re.sub(pattern, replacer, value)
        
        for key, value in paths_config.items():
            # First expand bash-style ${VAR:-default} syntax
            expanded = expand_bash_var(str(value))
            # Then expand standard $VAR syntax
            resolved_value = os.path.expandvars(expanded)
            # Convert to Path if it's a path
            resolved[key] = Path(resolved_value) if '/' in resolved_value or '\\' in resolved_value else resolved_value
        
        return resolved
    
    def _execute_phase(self, phase_name: str, phase_results: dict = None) -> dict:
        """Execute a phase module."""
        phase_dir = self.index_path / phase_name
        
        if not phase_dir.exists():
            print(f"{Colors.YELLOW}WARNING: Phase directory not found: {phase_dir}{Colors.NC}")
            return {"success": False, "error": f"Phase directory not found: {phase_dir}"}
        
        phase_index = phase_dir / 'index.py'
        if not phase_index.exists():
            print(f"{Colors.YELLOW}WARNING: Phase index.py not found: {phase_index}{Colors.NC}")
            return {"success": False, "error": f"Phase index.py not found: {phase_index}"}
        
        # Import and execute phase
        import importlib.util
        # Add phase directory parent to path BEFORE loading (for relative imports to work)
        # This ensures that when the module uses relative imports like "from .download import ...",
        # Python can resolve them correctly
        sys.path.insert(0, str(phase_dir.parent))
        
        # Use phase directory name as module name so relative imports resolve correctly
        # The module name should match the directory structure for relative imports to work
        module_name = f"{phase_name}.index"
        spec = importlib.util.spec_from_file_location(module_name, phase_index)
        module = importlib.util.module_from_spec(spec)
        
        # Set __package__ attribute so relative imports work
        # This tells Python what package this module belongs to
        module.__package__ = phase_name
        spec.loader.exec_module(module)
        
        # Prepare config for phase (include paths and previous phase results)
        phase_config = {**self.paths, **self.config.get(phase_name, {})}
        if phase_results:
            # Merge previous phase results into config so subsequent phases can access them
            phase_config.update(phase_results)
        
        # Call main function
        if hasattr(module, 'main'):
            result = module.main(phase_dir, phase_config)
            return result if isinstance(result, dict) else {"success": bool(result)}
        else:
            return {"success": False, "error": f"Phase {phase_name} has no main() function"}
    
    def execute(self) -> bool:
        """Execute all phases in order."""
        print(f"{Colors.BLUE}Starting Homerchy ISO Build...{Colors.NC}")
        print(f"{Colors.BLUE}Repository root: {self.paths.get('repo_root', 'N/A')}{Colors.NC}")
        
        children = self.config.get('children', [])
        execution_config = self.config.get('execution', {})
        continue_on_error = execution_config.get('continue_on_error', False)
        
        results = {}
        accumulated_results = {}
        
        for phase_name in children:
            print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
            result = self._execute_phase(phase_name, accumulated_results)
            results[phase_name] = result
            
            # Accumulate results for next phases (excluding internal fields)
            if result.get('success'):
                for key, value in result.items():
                    if key not in ['success', 'error']:
                        accumulated_results[key] = value
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                print(f"{Colors.RED}Phase {phase_name} failed: {error_msg}{Colors.NC}")
                
                if not continue_on_error:
                    print(f"{Colors.RED}Build aborted due to phase failure{Colors.NC}")
                    return False
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.NC}")
        print(f"{Colors.GREEN}All phases completed successfully!{Colors.NC}")
        return True


def main():
    """Main entry point."""
    index_path = Path(__file__).parent
    orchestrator = Orchestrator(index_path)
    success = orchestrator.execute()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
