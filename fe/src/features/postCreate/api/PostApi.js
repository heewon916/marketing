import { api } from "@/lib/Axios"

export async function requestDraftPost(sessionId) {
	if (!sessionId) {
		//throw new Error("세션 정보가 없어 임시 게시물을 조회할 수 없습니다.")
	}

	try {
		const response = await api.get(`/api/v1/contents/${sessionId}`)
		const data = response.data ?? {}
		console.log(data)
		const images = Array.isArray(data.images) ? data.images : []

		const sortedImages = [...images].sort((a, b) => {
			const aOrder = Number.isFinite(a?.display_order) ? a.display_order : Number.MAX_SAFE_INTEGER
			const bOrder = Number.isFinite(b?.display_order) ? b.display_order : Number.MAX_SAFE_INTEGER
			return aOrder - bOrder
		})

		return {
			sessionId: data.sessionId ?? sessionId,
			status: data.status ?? "",
			caption: data.caption ?? "",
			instagramUsername: data.instagramUsername ?? "",
			instagramProfileImageUrl: data.instagramProfileImageUrl ? `${import.meta.env.VITE_CLOUDFRONT_DOMAIN}${data.instagramProfileImageUrl}` : "",
			images: sortedImages.map((image, index) => ({
				id: image.id ?? `image-${index}`,
				url: image.filtered_url ? `${import.meta.env.VITE_CLOUDFRONT_DOMAIN}${image.filtered_url}` : "",
				displayOrder: image.display_order ?? index + 1,
			})),
		}
	} catch (error) {
		const errorMessage = error.response?.data?.message
		throw new Error(errorMessage || "임시 게시물 조회에 실패했습니다.", { cause: error })
	}
}

export async function requestEditDraftCaption(sessionId, caption) {
	if (!sessionId) {
		//throw new Error("세션 정보가 없어 캡션을 수정할 수 없습니다.")
	}

	try {
		const response = await api.patch(`/api/v1/contents/${sessionId}/edit`, {
			caption,
		})

		const data = response.data ?? {}
		console.log("EDIT", data)
		
		return {
			sessionId: data.session_id ?? sessionId,
			caption: data.caption ?? caption,
			updatedAt: data.updated_at ?? "",
		}
	} catch (error) {
		const errorMessage = error.response?.data?.message
		//throw new Error(errorMessage || "캡션 수정에 실패했습니다.", { cause: error })
	}
}
