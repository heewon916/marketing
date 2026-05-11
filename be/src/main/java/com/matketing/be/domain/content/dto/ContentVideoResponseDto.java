package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record ContentVideoResponseDto(
        @JsonProperty("video_recording_id")
        String videoRecordingId,
        @JsonProperty("extracted_frames")
        List<ExtractedFrame> extractedFrames
) {

    public record ExtractedFrame(
            @JsonProperty("image_id")
            String imageId,
            @JsonProperty("original_key")
            String originalKey
    ) {
    }
}
