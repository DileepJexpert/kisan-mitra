package com.kisanmitra.gateway.dto;

import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class UserDTO {
    private UUID id;
    private String phone;
    private String name;
    private String language;
    private String state;
    private String district;
    private String occupation;
    private String subscriptionTier;
}
