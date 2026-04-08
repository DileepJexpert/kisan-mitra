package com.kisanmitra.gateway.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class UpdateUserRequest {
    private String name;
    private String language;
    private String state;
    private String district;
    private String pincode;
    private String category;
    private String gender;
    private BigDecimal incomeAnnual;
    private BigDecimal landAcres;
    private String occupation;
    private String udyamNumber;
}
