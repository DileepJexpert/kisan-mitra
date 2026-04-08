package com.kisanmitra.gateway.controller;

import com.kisanmitra.gateway.dto.WhatsAppWebhookPayload;
import com.kisanmitra.gateway.service.WhatsAppService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/webhook")
@RequiredArgsConstructor
@Slf4j
public class WebhookController {

    private final WhatsAppService whatsAppService;

    @PostMapping("/whatsapp")
    public ResponseEntity<Map<String, String>> receiveWhatsApp(
            @RequestBody WhatsAppWebhookPayload payload) {
        log.info("WhatsApp webhook received: type={}", payload.getType());
        whatsAppService.processIncomingMessage(payload);
        return ResponseEntity.ok(Map.of("status", "received"));
    }

    @GetMapping("/whatsapp")
    public ResponseEntity<String> verifyWebhook(
            @RequestParam(value = "hub.challenge", required = false) String challenge) {
        // Gupshup/WhatsApp webhook verification
        return ResponseEntity.ok(challenge != null ? challenge : "OK");
    }
}
