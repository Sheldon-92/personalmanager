"""
Test suite for AI integration functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from pm.cli.commands.ai import ai_app, route, config_cmd, status


class TestAICommand:
    """Test AI command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_ai_route_with_query(self):
        """Test AI route command with a query."""
        with patch('pm.cli.commands.ai._process_ai_query') as mock_process:
            mock_process.return_value = {
                'service': 'claude',
                'query': 'test query',
                'response': 'test response',
                'status': 'success'
            }

            result = self.runner.invoke(ai_app, ['route', 'test query'])

            assert result.exit_code == 0
            mock_process.assert_called_once()

    def test_ai_route_json_output(self):
        """Test AI route command with JSON output."""
        with patch('pm.cli.commands.ai._process_ai_query') as mock_process:
            mock_process.return_value = {
                'service': 'claude',
                'query': 'test query',
                'response': 'test response',
                'status': 'success'
            }

            result = self.runner.invoke(ai_app, ['route', '--json', 'test query'])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['status'] == 'success'
            assert output['service'] == 'claude'

    def test_ai_route_service_selection(self):
        """Test AI route with specific service selection."""
        with patch('pm.cli.commands.ai._process_ai_query') as mock_process:
            mock_process.return_value = {
                'service': 'gemini',
                'query': 'test query',
                'response': 'gemini response',
                'status': 'success'
            }

            result = self.runner.invoke(ai_app, ['route', '--service=gemini', 'test query'])

            assert result.exit_code == 0
            mock_process.assert_called_with('gemini', 'test query', mock_process.call_args[0][2])

    def test_ai_config_list(self):
        """Test AI config list command."""
        with patch('pm.cli.commands.ai._list_ai_config') as mock_list:
            result = self.runner.invoke(ai_app, ['config', '--list'])

            assert result.exit_code == 0
            mock_list.assert_called_once()

    def test_ai_config_set(self):
        """Test AI config set command."""
        with patch('pm.core.config.Config.set') as mock_set:
            with patch('pm.core.config.Config.save') as mock_save:
                result = self.runner.invoke(ai_app, ['config', '--set', 'default_service=gemini'])

                assert result.exit_code == 0
                mock_set.assert_called_with('ai.default_service', 'gemini')
                mock_save.assert_called_once()

    def test_ai_config_get(self):
        """Test AI config get command."""
        with patch('pm.core.config.Config.get') as mock_get:
            mock_get.return_value = 'test_value'
            result = self.runner.invoke(ai_app, ['config', '--get', 'api_key'])

            assert result.exit_code == 0
            assert 'api_key: test_value' in result.output

    def test_ai_status(self):
        """Test AI status command."""
        with patch('pm.cli.commands.ai._check_service_config') as mock_check:
            mock_check.side_effect = [True, False]  # Claude configured, Gemini not

            result = self.runner.invoke(ai_app, ['status'])

            assert result.exit_code == 0
            assert mock_check.call_count == 2

    def test_ai_status_json(self):
        """Test AI status command with JSON output."""
        with patch('pm.cli.commands.ai._check_service_config') as mock_check:
            mock_check.side_effect = [True, False]

            result = self.runner.invoke(ai_app, ['status', '--json'])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert 'claude' in output
            assert 'gemini' in output
            assert output['claude']['configured'] is True
            assert output['gemini']['configured'] is False

    def test_process_ai_query_claude(self):
        """Test processing query with Claude service."""
        from pm.cli.commands.ai import _process_ai_query
        from pm.core.config import Config

        config = Mock(spec=Config)
        config.get.return_value = {'api_key': 'test_key'}

        result = _process_ai_query('claude', 'test query', config)

        assert result['service'] == 'claude'
        assert result['status'] == 'success'
        assert 'response' in result

    def test_process_ai_query_gemini(self):
        """Test processing query with Gemini service."""
        from pm.cli.commands.ai import _process_ai_query
        from pm.core.config import Config

        config = Mock(spec=Config)
        config.get.return_value = {'api_key': 'test_key'}

        result = _process_ai_query('gemini', 'test query', config)

        assert result['service'] == 'gemini'
        assert result['status'] == 'success'
        assert 'response' in result

    def test_process_ai_query_missing_api_key(self):
        """Test error when API key is missing."""
        from pm.cli.commands.ai import _process_ai_query
        from pm.core.config import Config

        config = Mock(spec=Config)
        config.get.return_value = {}

        with pytest.raises(ValueError, match="API key not configured"):
            _process_ai_query('claude', 'test query', config)

    def test_check_service_config(self):
        """Test service configuration checking."""
        from pm.cli.commands.ai import _check_service_config
        from pm.core.config import Config

        config = Mock(spec=Config)

        # Test configured service
        config.get.return_value = {'api_key': 'test_key'}
        assert _check_service_config('claude', config) is True

        # Test unconfigured service
        config.get.return_value = {}
        assert _check_service_config('claude', config) is False


class TestAIIntegration:
    """Integration tests for AI functionality."""

    @pytest.mark.integration
    def test_ai_command_in_main_cli(self):
        """Test that AI command is properly registered in main CLI."""
        from pm.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['ai', '--help'])

        assert result.exit_code == 0
        assert 'AI-powered assistant integrations' in result.output

    @pytest.mark.integration
    def test_end_to_end_ai_workflow(self):
        """Test complete AI workflow from configuration to query."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Set up configuration
            with patch('pm.core.config.Config.save'):
                result = runner.invoke(ai_app, ['config', '--set', 'default_service=claude'])
                assert result.exit_code == 0

            # Check status
            with patch('pm.cli.commands.ai._check_service_config') as mock_check:
                mock_check.return_value = True
                result = runner.invoke(ai_app, ['status'])
                assert result.exit_code == 0

            # Execute query
            with patch('pm.cli.commands.ai._process_ai_query') as mock_process:
                mock_process.return_value = {
                    'service': 'claude',
                    'query': 'test',
                    'response': 'response',
                    'status': 'success'
                }
                result = runner.invoke(ai_app, ['route', 'test'])
                assert result.exit_code == 0