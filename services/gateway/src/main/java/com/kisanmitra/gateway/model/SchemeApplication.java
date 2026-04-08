package com.kisanmitra.gateway.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "scheme_applications")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SchemeApplication {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "scheme_id", nullable = false)
    private UUID schemeId;

    @Column(length = 30)
    @Builder.Default
    private String status = "identified";

    @Column(name = "applied_at")
    private LocalDateTime appliedAt;

    @Column(name = "documents_submitted", columnDefinition = "jsonb")
    private String documentsSubmitted;

    @Column(columnDefinition = "text")
    private String notes;

    @Column(name = "next_action")
    private String nextAction;

    @Column(name = "next_deadline")
    private LocalDateTime nextDeadline;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
