package com.kisanmitra.gateway.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "scheduled_notifications")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScheduledNotification {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "notification_type", length = 30)
    private String notificationType;

    @Column(length = 20)
    @Builder.Default
    private String channel = "whatsapp";

    @Column(name = "message_template", nullable = false, columnDefinition = "text")
    private String messageTemplate;

    @Column(name = "message_params", columnDefinition = "jsonb")
    private String messageParams;

    @Column(name = "scheduled_at", nullable = false)
    private LocalDateTime scheduledAt;

    @Column(name = "sent_at")
    private LocalDateTime sentAt;

    @Column(length = 20)
    @Builder.Default
    private String status = "pending";

    @Column(name = "retry_count")
    @Builder.Default
    private Integer retryCount = 0;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}
