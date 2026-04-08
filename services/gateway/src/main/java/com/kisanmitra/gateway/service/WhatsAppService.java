package com.kisanmitra.gateway.service;

import com.kisanmitra.gateway.dto.ChatRequest;
import com.kisanmitra.gateway.dto.ChatResponse;
import com.kisanmitra.gateway.dto.WhatsAppWebhookPayload;
import com.kisanmitra.gateway.model.Conversation;
import com.kisanmitra.gateway.model.Message;
import com.kisanmitra.gateway.model.User;
import com.kisanmitra.gateway.repository.ConversationRepository;
import com.kisanmitra.gateway.repository.MessageRepository;
import com.kisanmitra.gateway.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class WhatsAppService {

    private final UserRepository userRepository;
    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final AIServiceClient aiServiceClient;
    private final NotificationService notificationService;

    @Value("${app.gupshup.api-key:}")
    private String gupshupApiKey;

    @Value("${app.gupshup.app-name:KisanMitraBot}")
    private String gupshupAppName;

    @Async
    public void processIncomingMessage(WhatsAppWebhookPayload webhook) {
        try {
            var payload = webhook.getPayload();
            if (payload == null) return;

            String phone = payload.getSource();
            if (phone != null && phone.startsWith("91") && phone.length() > 10) {
                phone = phone.substring(phone.length() - 10);
            }
            String messageType = payload.getType();
            String content = "";

            if (payload.getPayload() != null) {
                content = "text".equals(messageType)
                        ? payload.getPayload().getText()
                        : payload.getPayload().getUrl();
            }

            if (content == null || content.isBlank()) return;

            // Find or create user
            final String normalizedPhone = phone;
            User user = userRepository.findByPhone(normalizedPhone).orElseGet(() -> {
                User newUser = User.builder().phone(normalizedPhone).build();
                return userRepository.save(newUser);
            });
            user.setLastActiveAt(LocalDateTime.now());
            userRepository.save(user);

            // Find or create conversation
            List<Conversation> conversations = conversationRepository
                    .findByUserIdOrderByStartedAtDesc(user.getId());
            Conversation conv;
            if (!conversations.isEmpty() && conversations.get(0).getEndedAt() == null) {
                conv = conversations.get(0);
            } else {
                conv = Conversation.builder()
                        .userId(user.getId())
                        .channel("whatsapp")
                        .productCode("kisanmitra")
                        .build();
                conv = conversationRepository.save(conv);
            }

            // Save user message
            messageRepository.save(Message.builder()
                    .conversationId(conv.getId())
                    .role("user")
                    .content(content)
                    .contentType(messageType)
                    .language(user.getLanguage())
                    .build());

            // Call AI service
            ChatRequest chatReq = ChatRequest.builder()
                    .userId(user.getId().toString())
                    .message(content)
                    .language(user.getLanguage())
                    .channel("whatsapp")
                    .build();

            ChatResponse chatResp = aiServiceClient.chatWithAgent(chatReq);

            // Save agent response
            messageRepository.save(Message.builder()
                    .conversationId(conv.getId())
                    .role("agent")
                    .content(chatResp.getReplyText())
                    .contentType("text")
                    .language(user.getLanguage())
                    .agentName(chatResp.getAgentsUsed() != null && !chatResp.getAgentsUsed().isEmpty()
                            ? chatResp.getAgentsUsed().get(0) : null)
                    .build());

            // Update conversation message count
            conv.setMessageCount(conv.getMessageCount() + 2);
            conversationRepository.save(conv);

            // Send reply via WhatsApp
            sendMessage(payload.getSource(), chatResp.getReplyText());

            // Process follow-up actions (schedule notifications etc.)
            if (chatResp.getFollowUpActions() != null) {
                for (var action : chatResp.getFollowUpActions()) {
                    String actionType = (String) action.get("type");
                    if ("reminder".equals(actionType)) {
                        notificationService.scheduleNotification(
                                user.getId(), "reminder",
                                (String) action.get("message"),
                                "whatsapp",
                                LocalDateTime.parse((String) action.get("scheduled_at")));
                    }
                }
            }

            log.info("Processed WhatsApp message for user={}, agents={}",
                    user.getId(), chatResp.getAgentsUsed());

        } catch (Exception e) {
            log.error("Error processing WhatsApp message: {}", e.getMessage(), e);
        }
    }

    public void sendMessage(String phone, String text) {
        if (gupshupApiKey == null || gupshupApiKey.isBlank()) {
            log.info("Gupshup not configured. Would send to {}: {}", phone, text);
            return;
        }

        try {
            RestTemplate rest = new RestTemplate();
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
            headers.set("apikey", gupshupApiKey);

            MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
            body.add("channel", "whatsapp");
            body.add("source", "919876543210");
            body.add("destination", phone);
            body.add("src.name", gupshupAppName);
            body.add("message", String.format("{\"type\":\"text\",\"text\":\"%s\"}",
                    text.replace("\"", "\\\"")));

            HttpEntity<MultiValueMap<String, String>> entity = new HttpEntity<>(body, headers);
            rest.postForEntity("https://api.gupshup.io/wa/api/v1/msg", entity, String.class);
        } catch (Exception e) {
            log.error("Failed to send WhatsApp message to {}: {}", phone, e.getMessage());
        }
    }
}
