"""
Intent Matcher for PersonalManager

Handles natural language intent matching based on interaction patterns configuration.
"""

import json
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MatchResult:
    """Result of intent matching"""
    intent: str
    confidence: float
    command: str
    args: Dict[str, Any]
    confirm_message: Optional[str]


class IntentMatcher:
    """Intent matcher that processes natural language utterances and maps them to commands"""

    def __init__(self, patterns_file: Optional[str] = None):
        """
        Initialize the intent matcher

        Args:
            patterns_file: Path to interaction patterns JSON file.
                          If None, uses default template location.
        """
        self.patterns = {}
        self.intents = []

        if patterns_file is None:
            # Use default template location
            patterns_file = os.path.join(
                os.path.dirname(__file__),
                "../workspace/templates/interaction-patterns.json"
            )

        self.patterns_file = patterns_file
        self.load_patterns()

    def load_patterns(self) -> None:
        """Load interaction patterns from JSON file"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.patterns = data
                self.intents = data.get('intents', [])
        except FileNotFoundError:
            raise FileNotFoundError(f"Patterns file not found: {self.patterns_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in patterns file: {e}")

    def match_intent(self, utterance: str) -> MatchResult:
        """
        Match utterance to an intent and return result

        Args:
            utterance: Natural language input from user

        Returns:
            MatchResult with intent, confidence, command, args and confirm_message
        """
        utterance = utterance.strip()

        # Handle empty or whitespace-only utterances
        if not utterance:
            return MatchResult(
                intent="unknown",
                confidence=0.0,
                command="",
                args={},
                confirm_message="未识别的指令，请尝试其他表达方式"
            )

        best_match = None
        best_confidence = 0.0

        for intent_config in self.intents:
            confidence, args = self._calculate_match_confidence(utterance, intent_config)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = intent_config
                best_args = args

        if best_match is None or best_confidence == 0.0:
            # No match found
            return MatchResult(
                intent="unknown",
                confidence=0.0,
                command="",
                args={},
                confirm_message="未识别的指令，请尝试其他表达方式"
            )

        # Build command string with arguments
        command = self._build_command(best_match, best_args)

        # Get confirmation message if confidence is low
        confirm_message = None
        if best_confidence < 0.8:
            confirm_message = self._get_confirm_message(best_match, best_args)

        return MatchResult(
            intent=best_match['id'],
            confidence=best_confidence,
            command=command,
            args=best_args,
            confirm_message=confirm_message
        )

    def _calculate_match_confidence(self, utterance: str, intent_config: Dict) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate matching confidence for an intent configuration

        Returns:
            Tuple of (confidence_score, extracted_args)
        """
        confidence = 0.0
        args = {}

        # Check phrases for exact or partial matches
        phrases = intent_config.get('phrases', [])
        for phrase in phrases:
            phrase_lower = phrase.lower()
            utterance_lower = utterance.lower()

            if phrase_lower == utterance_lower:
                # Exact match
                confidence = max(confidence, 1.0)
            elif phrase_lower in utterance_lower or utterance_lower in phrase_lower:
                # Partial match
                if len(phrase_lower) > len(utterance_lower):
                    # Utterance is substring of phrase
                    ratio = len(utterance_lower) / len(phrase_lower)
                    confidence = max(confidence, 0.5 + ratio * 0.3)
                else:
                    # Phrase is substring of utterance
                    ratio = len(phrase_lower) / len(utterance_lower)
                    confidence = max(confidence, 0.5 + ratio * 0.3)

        # Check pattern matching if available
        pattern = intent_config.get('pattern')
        if pattern:
            try:
                match = re.search(pattern, utterance, re.IGNORECASE)
                if match:
                    # Pattern match found
                    pattern_confidence = 0.7
                    confidence = max(confidence, pattern_confidence)

                    # Extract named groups as arguments
                    groups = match.groupdict()
                    for key, value in groups.items():
                        if value is not None:
                            args[key] = value.strip()
            except re.error:
                # Invalid regex pattern, skip
                pass

        # Apply default values for args based on schema
        args_schema = intent_config.get('args_schema', {})
        for arg_name, arg_config in args_schema.items():
            if arg_name not in args and 'default' in arg_config:
                args[arg_name] = arg_config['default']

        return confidence, args

    def _build_command(self, intent_config: Dict, args: Dict[str, Any]) -> str:
        """Build command string from intent config and arguments"""
        command_template = intent_config.get('command', '')

        # Replace placeholders with actual argument values
        command = command_template
        for arg_name, arg_value in args.items():
            if arg_value is not None:
                placeholder = f"{{{arg_name}}}"
                command = command.replace(placeholder, str(arg_value))

        # Remove any remaining empty placeholders
        command = re.sub(r'\s*\{\w+\}\s*', ' ', command)
        command = re.sub(r'\s+', ' ', command).strip()

        return command

    def _get_confirm_message(self, intent_config: Dict, args: Dict[str, Any]) -> Optional[str]:
        """Get confirmation message for low confidence matches"""
        confirm_config = intent_config.get('confirm', {})

        # Use Chinese message by default, fallback to English
        message = confirm_config.get('low_confidence') or confirm_config.get('low_confidence_en')

        if message:
            # Replace placeholders with argument values
            for arg_name, arg_value in args.items():
                if arg_value is not None:
                    placeholder = f"{{{arg_name}}}"
                    message = message.replace(placeholder, str(arg_value))

        return message

    def get_supported_intents(self) -> List[str]:
        """Get list of all supported intent IDs"""
        return [intent['id'] for intent in self.intents]

    def get_intent_description(self, intent_id: str) -> Optional[str]:
        """Get description for a specific intent"""
        for intent in self.intents:
            if intent['id'] == intent_id:
                return intent.get('description')
        return None