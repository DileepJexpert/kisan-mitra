package com.kisanmitra.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ChatResponse {
    @JsonProperty("reply_text")
    private String replyText;

    @JsonProperty("reply_audio_base64")
    private String replyAudioBase64;

    @JsonProperty("agents_used")
    private List<String> agentsUsed;

    @JsonProperty("actions_taken")
    private List<String> actionsTaken;

    @JsonProperty("follow_up_actions")
    private List<Map<String, Object>> followUpActions;
}
