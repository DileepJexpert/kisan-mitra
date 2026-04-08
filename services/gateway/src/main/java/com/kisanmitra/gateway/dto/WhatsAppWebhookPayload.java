package com.kisanmitra.gateway.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class WhatsAppWebhookPayload {
    private String app;
    private Long timestamp;
    private Integer version;
    private String type;
    private Payload payload;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Payload {
        private String id;
        private String source;
        private String type;
        private MessagePayload payload;
        private Sender sender;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MessagePayload {
        private String text;
        private String url;
        private String caption;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Sender {
        private String phone;
        private String name;
    }
}
