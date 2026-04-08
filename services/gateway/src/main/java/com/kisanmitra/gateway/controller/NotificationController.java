package com.kisanmitra.gateway.controller;

import com.kisanmitra.gateway.model.ScheduledNotification;
import com.kisanmitra.gateway.repository.NotificationRepository;
import com.kisanmitra.gateway.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationRepository notificationRepository;
    private final NotificationService notificationService;

    @GetMapping
    public ResponseEntity<List<ScheduledNotification>> listNotifications(
            Authentication auth, @RequestParam(required = false) String status) {
        UUID userId = UUID.fromString(auth.getName());
        List<ScheduledNotification> notifications = status != null
                ? notificationRepository.findByUserIdAndStatus(userId, status)
                : notificationRepository.findByUserId(userId);
        return ResponseEntity.ok(notifications);
    }

    @PostMapping("/{id}/cancel")
    public ResponseEntity<Map<String, String>> cancelNotification(@PathVariable UUID id) {
        notificationService.cancelNotification(id);
        return ResponseEntity.ok(Map.of("status", "cancelled"));
    }
}
