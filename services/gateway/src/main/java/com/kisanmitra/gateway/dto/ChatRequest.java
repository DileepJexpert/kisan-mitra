package com.kisanmitra.gateway.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ChatRequest {
    private String userId;
    private String message;
    @Builder.Default
    private String language = "hi";
    @Builder.Default
    private String channel = "whatsapp";
    private String audioBase64;
}
