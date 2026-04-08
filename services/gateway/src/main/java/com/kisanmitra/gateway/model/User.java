package com.kisanmitra.gateway.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "users")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true, length = 15)
    private String phone;

    @Column(length = 100)
    private String name;

    @Column(length = 5)
    @Builder.Default
    private String language = "hi";

    @Column(length = 50)
    private String state;

    @Column(length = 100)
    private String district;

    @Column(length = 6)
    private String pincode;

    @Column(length = 20)
    private String category;

    @Column(length = 10)
    private String gender;

    @Column(name = "income_annual")
    private BigDecimal incomeAnnual;

    @Column(name = "land_acres")
    private BigDecimal landAcres;

    @Column(length = 50)
    private String occupation;

    @Column(name = "udyam_number", length = 30)
    private String udyamNumber;

    @Column(name = "aadhaar_reference", length = 50)
    private String aadhaarReference;

    @Column(name = "pan_reference", length = 20)
    private String panReference;

    @Column(name = "onboarded_at")
    @Builder.Default
    private LocalDateTime onboardedAt = LocalDateTime.now();

    @Column(name = "last_active_at")
    private LocalDateTime lastActiveAt;

    @Column(name = "subscription_tier", length = 20)
    @Builder.Default
    private String subscriptionTier = "free";

    @Column(name = "subscription_expires_at")
    private LocalDateTime subscriptionExpiresAt;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
