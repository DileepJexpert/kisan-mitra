package com.kisanmitra.gateway.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "disputes")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Dispute {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "buyer_name", length = 200)
    private String buyerName;

    @Column(name = "buyer_gstin", length = 20)
    private String buyerGstin;

    @Column(name = "invoice_number", length = 50)
    private String invoiceNumber;

    @Column(name = "invoice_date")
    private LocalDate invoiceDate;

    @Column(name = "invoice_amount")
    private BigDecimal invoiceAmount;

    @Column(name = "due_date")
    private LocalDate dueDate;

    @Column(name = "days_overdue")
    private Integer daysOverdue;

    @Column(name = "interest_amount")
    private BigDecimal interestAmount;

    @Column(name = "total_claim")
    private BigDecimal totalClaim;

    @Column(name = "legal_notice_generated")
    @Builder.Default
    private Boolean legalNoticeGenerated = false;

    @Column(name = "legal_notice_sent_at")
    private LocalDateTime legalNoticeSentAt;

    @Column(name = "odr_case_filed")
    @Builder.Default
    private Boolean odrCaseFiled = false;

    @Column(name = "odr_case_id", length = 50)
    private String odrCaseId;

    @Column(length = 30)
    @Builder.Default
    private String status = "new";

    @Column(name = "resolution_amount")
    private BigDecimal resolutionAmount;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
