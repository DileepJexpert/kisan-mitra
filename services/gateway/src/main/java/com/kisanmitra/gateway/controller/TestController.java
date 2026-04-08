package com.kisanmitra.gateway.controller;

import com.kisanmitra.gateway.dto.ChatRequest;
import com.kisanmitra.gateway.dto.ChatResponse;
import com.kisanmitra.gateway.service.AIServiceClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/test")
@RequiredArgsConstructor
public class TestController {

    private final AIServiceClient aiServiceClient;

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> testChat(@RequestBody ChatRequest request) {
        ChatResponse response = aiServiceClient.chatWithAgent(request);
        return ResponseEntity.ok(response);
    }
}
