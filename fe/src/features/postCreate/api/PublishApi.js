import { api } from "@/lib/Axios"

export async function requestPublishStart(sessionId) {
	if (!sessionId) {
		throw new Error("세션 정보가 없어 발행을 시작할 수 없습니다.")
	}

	try {
		const response = await api.post(`/api/v1/contents/${sessionId}/publish`)
		const data = response.data ?? {}
		console.log(data)
		return data
	} catch (error) {
		const errorMessage = error.response?.data?.message
		throw new Error(errorMessage || "발행 시작 요청에 실패했습니다.", { cause: error })
	}
}

export async function requestPublishStatus(sessionId) {
	if (!sessionId) {
		throw new Error("세션 정보가 없어 발행 상태를 조회할 수 없습니다.")
	}

	try {
		const response = await api.get(`/api/v1/contents/${sessionId}/publish/status`)
		const data = response.data ?? {}
		console.log(data)

		return {
			contentId: data.content_id ?? "",
			publishProgress: data.publish_progress ?? "",
			instagramMediaId: data.instagram_media_id ?? "",
			instagramPermalink: data.instagram_permalink ?? "",
		}
	} catch (error) {
		const errorMessage = error.response?.data?.message
		throw new Error(errorMessage || "발행 상태 조회에 실패했습니다.", { cause: error })
	}
}
