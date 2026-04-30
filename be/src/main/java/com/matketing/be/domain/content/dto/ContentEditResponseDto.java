package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.entity.Content;

public record ContentEditResponseDto(
        Long id,
        String caption
) {

    public static ContentEditResponseDto from(Content content) {
        return new ContentEditResponseDto(content.getId(), content.getCaption());
    }
}
