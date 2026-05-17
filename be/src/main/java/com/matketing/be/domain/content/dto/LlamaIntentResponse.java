package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonAlias;

public record LlamaIntentResponse(
    @JsonAlias("is_create_post")
    boolean isCreatePost,
    String reply
) {
}
