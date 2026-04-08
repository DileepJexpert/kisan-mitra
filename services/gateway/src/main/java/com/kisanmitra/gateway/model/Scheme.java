package com.kisanmitra.gateway.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "schemes")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Scheme {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "scheme_code", unique = true, nullable = false, length = 50)
    private String schemeCode;

    @Column(name = "name_en", nullable = false, length = 200)
    private String nameEn;

    @Column(name = "name_hi", length = 200)
    private String nameHi;

    @Column(length = 100)
    private String ministry;

    @Column(length = 100)
    private String department;

    @Column(name = "scheme_type", length = 30)
    private String schemeType;

    @Column(length = 50)
    private String state;

    @Column(length = 50)
    private String sector;

    @Column(length = 50)
    private String subsector;

    @Column(name = "eligibility_criteria", columnDefinition = "jsonb")
    private String eligibilityCriteria;

    @Column(name = "benefit_type", length = 30)
    private String benefitType;

    @Column(name = "subsidy_percentage")
    private BigDecimal subsidyPercentage;

    @Column(name = "max_subsidy_amount")
    private BigDecimal maxSubsidyAmount;

    @Column(name = "loan_amount_max")
    private BigDecimal loanAmountMax;

    @Column(name = "interest_subsidy")
    private BigDecimal interestSubsidy;

    @Column(name = "application_url", length = 500)
    private String applicationUrl;

    @Column(name = "documents_required", columnDefinition = "jsonb")
    private String documentsRequired;

    @Column(name = "application_process", columnDefinition = "text")
    private String applicationProcess;

    @Column(name = "description_en", columnDefinition = "text")
    private String descriptionEn;

    @Column(name = "description_hi", columnDefinition = "text")
    private String descriptionHi;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column(name = "source_url", length = 500)
    private String sourceUrl;

    @Column(name = "last_verified_at")
    private LocalDateTime lastVerifiedAt;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
