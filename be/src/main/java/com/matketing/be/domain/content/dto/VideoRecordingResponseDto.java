package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.entity.VideoRecording;
import java.util.UUID;

public record VideoRecordingResponseDto(
        UUID id,
        String s3Key
) {

    public static VideoRecordingResponseDto from(VideoRecording videoRecording) {
        return new VideoRecordingResponseDto(videoRecording.getId(), videoRecording.getS3Key());
    }
}
