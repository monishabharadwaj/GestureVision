from __future__ import annotations

"""Voice + gesture conversation flows for Beauty and Dandelion."""

from dataclasses import dataclass, field
from enum import Enum

from gesturevision.accessibility.learning import explain_topic, google_search_url
from gesturevision.accessibility.youtube_music import youtube_play_url


class ConversationMode(str, Enum):
    IDLE = "idle"
    MUSIC = "music"
    LEARN = "learn"
    FREE = "free"


@dataclass
class ConversationResult:
    """Outcome after the user speaks during a conversation."""

    reply: str
    open_url: str | None = None
    visual_detail: str = ""
    mode: ConversationMode = ConversationMode.IDLE
    direct_play: bool = False


@dataclass
class ConversationManager:
    """Guides blind/deaf users through music, learning, and free requests."""

    mode: ConversationMode = ConversationMode.IDLE
    last_agent_prompt: str = ""
    last_user_text: str = ""

    def start_music(self) -> str:
        self.mode = ConversationMode.MUSIC
        self.last_agent_prompt = (
            "Music mode. What song would you like? Say the song name or artist. "
            "I will play it directly."
        )
        return self.last_agent_prompt

    def start_learn(self) -> str:
        self.mode = ConversationMode.LEARN
        self.last_agent_prompt = (
            "Learning mode. What do you want to learn? "
            "Speak your topic now — for example: planets, cooking, or history."
        )
        return self.last_agent_prompt

    def start_free(self) -> str:
        self.mode = ConversationMode.FREE
        self.last_agent_prompt = (
            "Tell me what you want. You can say open YouTube, play a song, "
            "or ask to learn something."
        )
        return self.last_agent_prompt

    def is_active(self) -> bool:
        return self.mode != ConversationMode.IDLE

    def handle_utterance(self, text: str) -> ConversationResult:
        self.last_user_text = text.strip()
        if not self.last_user_text:
            return ConversationResult(
                reply="I did not hear you. Please try again.",
                mode=self.mode,
            )

        if self.mode == ConversationMode.MUSIC:
            return self._handle_music(self.last_user_text)
        if self.mode == ConversationMode.LEARN:
            return self._handle_learn(self.last_user_text)
        if self.mode == ConversationMode.FREE:
            return self._handle_free(self.last_user_text)

        return ConversationResult(reply="", mode=ConversationMode.IDLE)

    def _handle_music(self, text: str) -> ConversationResult:
        song = text
        self.mode = ConversationMode.IDLE
        url, direct = youtube_play_url(song)
        if direct:
            reply = f"Now playing {song}."
        else:
            reply = f"Could not find an exact match. Opening YouTube search for {song}."
        return ConversationResult(
            reply=reply,
            open_url=url,
            mode=ConversationMode.IDLE,
            direct_play=direct,
        )

    def _handle_learn(self, text: str) -> ConversationResult:
        topic = text
        explanation = explain_topic(topic, max_chars=900)
        self.mode = ConversationMode.IDLE
        short_reply = f"Here is what I found about {topic}."
        return ConversationResult(
            reply=short_reply,
            visual_detail=explanation,
            open_url=google_search_url(f"learn about {topic}"),
            mode=ConversationMode.IDLE,
        )

    def _handle_free(self, text: str) -> ConversationResult:
        lowered = text.lower()
        self.mode = ConversationMode.IDLE

        if any(word in lowered for word in ("youtube", "you tube", "video")):
            if any(word in lowered for word in ("song", "music", "play")):
                return ConversationResult(
                    reply="What song should I search on YouTube?",
                    open_url=None,
                    mode=ConversationMode.MUSIC,
                )
            return ConversationResult(
                reply="Opening YouTube.",
                open_url="https://www.youtube.com",
                mode=ConversationMode.IDLE,
            )

        if any(word in lowered for word in ("learn", "teach", "explain", "what is")):
            topic = (
                lowered.replace("i want to learn", "")
                .replace("teach me", "")
                .replace("explain", "")
                .replace("what is", "")
                .strip()
            )
            if topic:
                explanation = explain_topic(topic, max_chars=900)
                return ConversationResult(
                    reply=f"Here is what I found about {topic}.",
                    visual_detail=explanation,
                    open_url=google_search_url(topic),
                    mode=ConversationMode.IDLE,
                )
            self.mode = ConversationMode.LEARN
            return ConversationResult(
                reply="What do you want to learn about?",
                mode=ConversationMode.LEARN,
            )

        if any(word in lowered for word in ("music", "song", "play")):
            self.mode = ConversationMode.MUSIC
            return ConversationResult(
                reply="What song would you like?",
                mode=ConversationMode.MUSIC,
            )

        if "chrome" in lowered or "google" in lowered:
            return ConversationResult(
                reply="Opening Chrome.",
                open_url="https://www.google.com",
                mode=ConversationMode.IDLE,
            )

        return ConversationResult(
            reply=f"I heard: {text}. Opening a search.",
            open_url=google_search_url(text),
            mode=ConversationMode.IDLE,
        )

    def reset(self) -> None:
        self.mode = ConversationMode.IDLE
        self.last_agent_prompt = ""
        self.last_user_text = ""
