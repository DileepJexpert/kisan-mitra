package com.kisanmitra.gateway.service;

import com.kisanmitra.gateway.dto.ChatRequest;
import com.kisanmitra.gateway.dto.ChatResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.Collections;

@Service
@Slf4j
public class AIServiceClient {

    private final RestTemplate restTemplate;
    private final String aiServiceUrl;

    public AIServiceClient(
            RestTemplateBuilder builder,
            @Value("${app.ai-service.url}") String aiServiceUrl,
            @Value("${app.ai-service.timeout-seconds:30}") int timeoutSeconds) {
        this.aiServiceUrl = aiServiceUrl;
        this.restTemplate = builder
                .connectTimeout(Duration.ofSeconds(5))
                .readTimeout(Duration.ofSeconds(timeoutSeconds))
                .build();
    }

    public ChatResponse chatWithAgent(ChatRequest request) {
        String url = aiServiceUrl + "/ai/v1/agent/chat";
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ChatRequest> entity = new HttpEntity<>(request, headers);

            ChatResponse response = restTemplate.postForObject(url, entity, ChatResponse.class);
            if (response != null) {
                return response;
            }
            return fallbackResponse("Service returned empty response");
        } catch (RestClientException e) {
            log.error("AI service call failed: {}", e.getMessage());
            return fallbackResponse(e.getMessage());
        }
    }

    private ChatResponse fallbackResponse(String error) {
        ChatResponse response = new ChatResponse();
        response.setReplyText("Kuch technical issue hai, please thodi der baad try karein. 🙏");
        response.setAgentsUsed(Collections.emptyList());
        response.setActionsTaken(Collections.emptyList());
        response.setFollowUpActions(Collections.emptyList());
        log.warn("Using fallback response due to: {}", error);
        return response;
    }
}
