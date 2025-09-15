"""
Plugin Loader - Main entry point for PM plugin system
Demonstrates dynamic plugin loading, permission checking, and hook registration
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pm.plugins.sdk import (
    PluginLoader,
    PluginConfigManager,
    HookType,
    HookContext
)

# Import integration logging
try:
    from pm.obs.integration_logger import (
        get_integration_logger, trace_plugin_operation,
        HandlerStatus, PluginStatus, MetricsStatus
    )
except ImportError:
    # Fallback for standalone usage
    def get_integration_logger():
        return None
    def trace_plugin_operation(*args, **kwargs):
        return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PluginSystem:
    """Main plugin system manager"""

    def __init__(self):
        """Initialize plugin system"""
        self.loader = PluginLoader()
        self.config_manager = PluginConfigManager()
        self.loaded_plugins = []

    async def initialize(self) -> bool:
        """Initialize the plugin system"""
        logger.info("=" * 60)
        logger.info("PM Plugin System v0.1.0 - Initializing")
        logger.info("=" * 60)

        # Discover available plugins
        logger.info("\nDiscovering plugins...")
        plugins = self.loader.discover_plugins()
        logger.info(f"Found {len(plugins)} plugin(s)")

        for plugin_path in plugins:
            logger.info(f"  - {plugin_path.name}")

        return True

    async def load_plugins(self) -> Dict[str, Any]:
        """Load all discovered plugins"""
        integration_logger = get_integration_logger()

        logger.info("\n" + "=" * 60)
        logger.info("Loading Plugins")
        logger.info("=" * 60)

        results = {
            "loaded": [],
            "failed": [],
            "total": 0
        }

        plugins = self.loader.discover_plugins()
        results["total"] = len(plugins)

        for plugin_path in plugins:
            plugin_name = plugin_path.stem if plugin_path.is_file() else plugin_path.name
            req_id = None

            if integration_logger:
                req_id = integration_logger.generate_request_id("plugin")
                integration_logger.start_request(req_id, f"PluginLoad:{plugin_name}")

            try:
                logger.info(f"\nLoading plugin: {plugin_path.name}")
                logger.info("-" * 40)

                # Load configuration
                if integration_logger and req_id:
                    with integration_logger.time_component(req_id, "config_load"):
                        config = self.config_manager.load_config(plugin_name)
                else:
                    config = self.config_manager.load_config(plugin_name)

                # Load plugin
                if integration_logger and req_id:
                    with integration_logger.time_component(req_id, "plugin_load"):
                        success = await self.loader.load_plugin(plugin_path, config)
                else:
                    success = await self.loader.load_plugin(plugin_path, config)

                if success:
                    results["loaded"].append(plugin_name)
                    self.loaded_plugins.append(plugin_name)
                    logger.info(f"✓ Successfully loaded: {plugin_name}")

                    if integration_logger and req_id:
                        integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                        integration_logger.update_plugin_status(req_id, PluginStatus.LOADED)
                        integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)
                else:
                    results["failed"].append(plugin_name)
                    logger.error(f"✗ Failed to load: {plugin_name}")

                    if integration_logger and req_id:
                        integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                        integration_logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR)

            except Exception as e:
                results["failed"].append(plugin_name)
                logger.error(f"✗ Exception loading {plugin_name}: {e}")

                if integration_logger and req_id:
                    integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                    integration_logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR)

            finally:
                if integration_logger and req_id:
                    integration_logger.complete_request(req_id)

        return results

    async def demonstrate_permissions(self) -> None:
        """Demonstrate permission checking"""
        logger.info("\n" + "=" * 60)
        logger.info("Permission Declaration Check")
        logger.info("=" * 60)

        for plugin_name, plugin in self.loader.plugins.items():
            metadata = plugin._metadata
            logger.info(f"\nPlugin: {plugin_name}")
            logger.info(f"  Version: {metadata.version}")
            logger.info(f"  Required Permissions:")

            for permission in metadata.required_permissions:
                logger.info(f"    - {permission.value}")

            # Check sandbox access
            sandbox = self.loader.sandboxes[plugin_name]
            logger.info(f"  Permission Checks:")

            # Simulate permission checks
            from pm.plugins.sdk import PluginPermission
            test_permissions = [
                PluginPermission.READ_DATA,
                PluginPermission.WRITE_DATA,
                PluginPermission.NETWORK_ACCESS
            ]

            for perm in test_permissions:
                has_perm = sandbox.check_permission(perm)
                status = "✓ GRANTED" if has_perm else "✗ DENIED"
                logger.info(f"    - {perm.value}: {status}")

    async def demonstrate_hooks(self) -> None:
        """Demonstrate hook system"""
        logger.info("\n" + "=" * 60)
        logger.info("Hook System Demonstration")
        logger.info("=" * 60)

        # Show registered hooks
        hook_summary = self.loader.hook_manager.get_hook_summary()
        logger.info("\nRegistered Hooks:")

        for hook_type, info in hook_summary.items():
            if info["count"] > 0:
                logger.info(f"  {hook_type}:")
                for handler in info["handlers"]:
                    logger.info(f"    - {handler}")

        # Execute sample hooks
        logger.info("\nExecuting Sample Hooks:")
        integration_logger = get_integration_logger()

        # Test report generation hook
        logger.info("\n1. Testing POST_REPORT_GENERATE hook:")
        req_id = None
        if integration_logger:
            req_id = integration_logger.generate_request_id("hook")
            integration_logger.start_request(req_id, "HookExec:POST_REPORT_GENERATE")

        try:
            context = HookContext(
                hook_type=HookType.POST_REPORT_GENERATE,
                data={
                    "report_data": {
                        "title": "Test Report",
                        "type": "demo",
                        "summary": "This is a demonstration report",
                        "content": {"test": "data", "timestamp": datetime.now().isoformat()}
                    }
                }
            )

            if integration_logger and req_id:
                with integration_logger.time_component(req_id, "hook_execution"):
                    result = await self.loader.execute_hook(HookType.POST_REPORT_GENERATE, context)
            else:
                result = await self.loader.execute_hook(HookType.POST_REPORT_GENERATE, context)

            if hasattr(result, 'data') and "exported_files" in result.data:
                logger.info(f"   Report exported to: {result.data['exported_files']}")

            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                integration_logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
                integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

        except Exception as e:
            logger.error(f"   Hook execution failed: {e}")
            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                integration_logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR)

        finally:
            if integration_logger and req_id:
                integration_logger.complete_request(req_id)

        # Test recommendation hook
        logger.info("\n2. Testing PRE_RECOMMENDATION hook:")
        req_id = None
        if integration_logger:
            req_id = integration_logger.generate_request_id("hook")
            integration_logger.start_request(req_id, "HookExec:PRE_RECOMMENDATION")

        try:
            context = HookContext(
                hook_type=HookType.PRE_RECOMMENDATION,
                data={
                    "user_id": "demo_user",
                    "context": {"category": "task", "tags": ["important"]}
                }
            )

            if integration_logger and req_id:
                with integration_logger.time_component(req_id, "hook_execution"):
                    result = await self.loader.execute_hook(HookType.PRE_RECOMMENDATION, context)
            else:
                result = await self.loader.execute_hook(HookType.PRE_RECOMMENDATION, context)

            if hasattr(result, 'data') and "custom_recommendations" in result.data:
                recs = result.data["custom_recommendations"]
                logger.info(f"   Generated {len(recs)} recommendations")

            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                integration_logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
                integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

        except Exception as e:
            logger.error(f"   Hook execution failed: {e}")
            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                integration_logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR)

        finally:
            if integration_logger and req_id:
                integration_logger.complete_request(req_id)

    async def show_capability_matrix(self) -> Dict[str, Any]:
        """Generate and display capability matrix"""
        logger.info("\n" + "=" * 60)
        logger.info("Plugin Capability Matrix")
        logger.info("=" * 60)

        matrix = {
            "plugins": {},
            "capabilities": {
                "permissions": {},
                "hooks": {},
                "algorithms": []
            }
        }

        for plugin_name, plugin in self.loader.plugins.items():
            metadata = plugin._metadata

            # Plugin summary
            plugin_info = {
                "version": metadata.version,
                "author": metadata.author,
                "description": metadata.description,
                "state": plugin.state.value,
                "permissions": [p.value for p in metadata.required_permissions],
                "hooks": {k.value: v for k, v in metadata.hooks.items()},
                "config": plugin.config
            }

            matrix["plugins"][plugin_name] = plugin_info

            # Aggregate capabilities
            for perm in metadata.required_permissions:
                if perm.value not in matrix["capabilities"]["permissions"]:
                    matrix["capabilities"]["permissions"][perm.value] = []
                matrix["capabilities"]["permissions"][perm.value].append(plugin_name)

            for hook_type in metadata.hooks.keys():
                if hook_type.value not in matrix["capabilities"]["hooks"]:
                    matrix["capabilities"]["hooks"][hook_type.value] = []
                matrix["capabilities"]["hooks"][hook_type.value].append(plugin_name)

            # Special capabilities
            if plugin_name == "custom_recommender":
                matrix["capabilities"]["algorithms"] = plugin.config.get("algorithm", [])

        # Display matrix
        logger.info("\nCapability Summary:")
        logger.info("-" * 40)

        logger.info("\nPermissions Coverage:")
        for perm, plugins in matrix["capabilities"]["permissions"].items():
            logger.info(f"  {perm}: {', '.join(plugins)}")

        logger.info("\nHook Coverage:")
        for hook, plugins in matrix["capabilities"]["hooks"].items():
            logger.info(f"  {hook}: {', '.join(plugins)}")

        logger.info("\nPlugin Details:")
        for plugin_name, info in matrix["plugins"].items():
            logger.info(f"\n  {plugin_name} v{info['version']}")
            logger.info(f"    State: {info['state']}")
            logger.info(f"    Permissions: {len(info['permissions'])}")
            logger.info(f"    Hooks: {sum(len(v) for v in info['hooks'].values())}")

        return matrix

    async def test_plugin_functionality(self) -> None:
        """Test actual plugin functionality"""
        logger.info("\n" + "=" * 60)
        logger.info("Plugin Functionality Test")
        logger.info("=" * 60)

        # Test Report Exporter
        if "report_exporter" in self.loader.plugins:
            logger.info("\nTesting Report Exporter:")
            plugin = self.loader.plugins["report_exporter"]

            test_report = {
                "title": "Plugin System Test Report",
                "type": "system_test",
                "summary": "Validating plugin system functionality",
                "content": {
                    "plugins_loaded": len(self.loader.plugins),
                    "hooks_registered": sum(
                        len(hooks) for hooks in self.loader.hook_manager.hooks.values()
                    ),
                    "test_timestamp": datetime.now().isoformat()
                }
            }

            exported = await plugin.export_report(test_report, ["json", "markdown"])
            logger.info(f"  Exported files:")
            for format_type, path in exported.items():
                logger.info(f"    - {format_type}: {path}")

            stats = plugin.get_export_statistics()
            logger.info(f"  Export statistics: {stats['stats']['total_exports']} total exports")

        # Test Custom Recommender
        if "custom_recommender" in self.loader.plugins:
            logger.info("\nTesting Custom Recommender:")
            plugin = self.loader.plugins["custom_recommender"]

            recommendations = await plugin.generate_recommendations(
                user_id="test_user",
                context={"category": "task", "tags": ["urgent", "important"]}
            )

            logger.info(f"  Generated {len(recommendations)} recommendations")
            for i, rec in enumerate(recommendations[:3], 1):
                logger.info(f"    {i}. {rec['item']['name']} (confidence: {rec['confidence']:.2f})")

            metrics = plugin.get_recommendation_metrics()
            logger.info(f"  Algorithm: {metrics['config']['algorithm']}")
            logger.info(f"  Total recommendations: {metrics['metrics']['total_recommendations']}")

    async def generate_load_evidence(self) -> Dict[str, Any]:
        """Generate load evidence for verification"""
        logger.info("\n" + "=" * 60)
        logger.info("Generating Load Evidence")
        logger.info("=" * 60)

        evidence = {
            "timestamp": datetime.now().isoformat(),
            "system_version": "0.1.0",
            "plugins_loaded": len(self.loader.plugins),
            "hooks_registered": sum(len(h) for h in self.loader.hook_manager.hooks.values()),
            "plugin_details": [],
            "permission_checks": [],
            "hook_executions": [],
            "metrics": {}
        }

        # Plugin details
        for plugin_name, plugin in self.loader.plugins.items():
            metadata = plugin._metadata
            sandbox = self.loader.sandboxes[plugin_name]

            plugin_detail = {
                "name": plugin_name,
                "version": metadata.version,
                "state": plugin.state.value,
                "permissions_requested": [p.value for p in metadata.required_permissions],
                "hooks_registered": sum(len(v) for v in metadata.hooks.values()),
                "access_summary": sandbox.get_access_summary()
            }
            evidence["plugin_details"].append(plugin_detail)

            # Add permission checks
            for log in sandbox.access_log[-5:]:  # Last 5 checks
                evidence["permission_checks"].append({
                    "plugin": plugin_name,
                    "permission": log["permission"],
                    "granted": log["granted"],
                    "timestamp": log["timestamp"]
                })

        # Hook execution summary
        for hook_type in HookType:
            handlers = self.loader.hook_manager.hooks[hook_type]
            if handlers:
                evidence["hook_executions"].append({
                    "hook": hook_type.value,
                    "handler_count": len(handlers),
                    "handlers": [h[1] for h in handlers]
                })

        # Metrics
        evidence["metrics"] = {
            "total_plugins": len(self.loader.plugins),
            "total_hooks": sum(len(h) for h in self.loader.hook_manager.hooks.values()),
            "total_permission_checks": sum(
                len(self.loader.sandboxes[p].access_log)
                for p in self.loader.plugins
            ),
            "plugin_states": {
                plugin_name: plugin.state.value
                for plugin_name, plugin in self.loader.plugins.items()
            }
        }

        logger.info(f"\nEvidence Summary:")
        logger.info(f"  Plugins Loaded: {evidence['plugins_loaded']}")
        logger.info(f"  Hooks Registered: {evidence['hooks_registered']}")
        logger.info(f"  Permission Checks: {evidence['metrics']['total_permission_checks']}")

        return evidence

    async def run(self) -> Dict[str, Any]:
        """Run the complete plugin system demonstration"""
        try:
            # Initialize
            await self.initialize()

            # Load plugins
            load_results = await self.load_plugins()

            # Demonstrate features
            await self.demonstrate_permissions()
            await self.demonstrate_hooks()
            capability_matrix = await self.show_capability_matrix()
            await self.test_plugin_functionality()

            # Generate evidence
            evidence = await self.generate_load_evidence()

            # Prepare final output
            output = {
                "status": "success",
                "command": "T-PLUGIN.complete",
                "data": {
                    "artifacts": [
                        "src/pm/plugins/sdk.py",
                        "src/pm/plugins/examples/report_exporter.py",
                        "src/pm/plugins/examples/custom_recommender.py",
                        "docs/plugins/SDK_GUIDE.md"
                    ],
                    "run_cmds": ["python -m pm.plugins.loader"],
                    "metrics": {
                        "plugins_loaded": len(self.loader.plugins),
                        "hooks_registered": evidence["hooks_registered"]
                    }
                },
                "metadata": {
                    "version": "0.1.0",
                    "execution_time": datetime.now().isoformat(),
                    "load_results": load_results,
                    "capability_matrix": capability_matrix,
                    "evidence": evidence
                }
            }

            # Save evidence
            evidence_file = Path("/tmp/plugin_load_evidence.json")
            with open(evidence_file, 'w') as f:
                json.dump(evidence, f, indent=2)
            logger.info(f"\nLoad evidence saved to: {evidence_file}")

            # Print final output
            logger.info("\n" + "=" * 60)
            logger.info("FINAL OUTPUT")
            logger.info("=" * 60)
            print(json.dumps(output, indent=2))

            return output

        except Exception as e:
            logger.error(f"Plugin system error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

        finally:
            # Cleanup
            logger.info("\nShutting down plugins...")
            for plugin_name in self.loaded_plugins:
                await self.loader.unload_plugin(plugin_name)


async def main():
    """Main entry point"""
    system = PluginSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())