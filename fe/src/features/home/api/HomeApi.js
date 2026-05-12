import { api } from '@/lib/Axios.js';

function createRequestId() {
	if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
		return crypto.randomUUID();
	}

	return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export async function requestSpeechToText(audioFile) {
	try {
		const formData = new FormData();
		formData.append('audio_file', audioFile);

		const response = await api.post('/api/v1/contents/stt', formData, {
			headers: {
				'Content-Type': 'multipart/form-data',
			},
		});

		if (response.data?.status === 'TEXT_RECOGNIZED') {
			return response.data.utterance || '';
		}

		throw new Error('음성 인식 실패: 예상치 못한 응답 형식');
	} catch (error) {
		const errorCode = error.response?.data?.code;
		const errorMessage = error.response?.data?.message;

		if (errorCode === 'INVALID_AUDIO_FILE') {
			throw new Error('지원하지 않는 음성 파일입니다.', { cause: error });
		} else if (errorCode === 'STT_FAILED') {
			throw new Error('음성 인식에 실패했습니다. 다시 녹음해 주세요.', { cause: error });
		} else if (error.response?.status === 401) {
			throw new Error('인증이 필요합니다.', { cause: error });
		}

		throw new Error(errorMessage || '음성 인식 중 오류가 발생했습니다.', { cause: error });
	}
}

export async function requestCaptionGeneration(utterance, requestId = createRequestId()) {
	try {
		const response = await api.post('/api/v1/contents/caption', {
			request_id: requestId,
			utterance,
		});

		const data = response.data ?? {};

		if (data.status && data.status !== 'TEXT_GENERATED') {
			throw new Error('게시글 생성이 아직 완료되지 않았습니다.');
		}

		return {
			requestId,
			sessionId: data.session_id ?? '',
			status: data.status ?? '',
			guideText: data.guide_text ?? '',
			caption: data.caption ?? '',
		};
	} catch (error) {
		const errorMessage = error.response?.data?.message;
		throw new Error(errorMessage || '게시글 생성 요청에 실패했습니다.', { cause: error });
	}
}
