package com.matketing.be.domain.content.util;

public final class KmaGridConverter {

    // 기상청 단기예보 API에서 사용하는 Lambert Conformal Conic 격자계 상수.
    // 위경도(WGS84)를 기상청 격자 좌표(nx, ny)로 변환할 때 공식 예제와 동일한 값을 사용한다.
    private static final double RE = 6371.00877;
    private static final double GRID = 5.0;
    private static final double SLAT1 = 30.0;
    private static final double SLAT2 = 60.0;
    private static final double OLON = 126.0;
    private static final double OLAT = 38.0;
    private static final double XO = 210.0 / GRID;
    private static final double YO = 675.0 / GRID;

    private KmaGridConverter() {
    }

    /**
     * 위경도 좌표를 기상청 단기예보 API의 격자 좌표로 변환한다.
     *
     * @param longitude 경도
     * @param latitude 위도
     * @return 기상청 격자 좌표
     */
    public static Grid convert(double longitude, double latitude) {
        // 도(degree) 단위의 기준값을 삼각함수 계산에 필요한 라디안 단위로 바꾼다.
        double degrad = Math.PI / 180.0;
        double re = RE / GRID;
        double slat1 = SLAT1 * degrad;
        double slat2 = SLAT2 * degrad;
        double olon = OLON * degrad;
        double olat = OLAT * degrad;

        // 투영 원뿔의 기울기(sn), 축척 보정값(sf), 기준점까지의 거리(ro)를 계산한다.
        // 이 세 값은 기상청 Lambert 격자계에서 모든 좌표 변환의 기준이 된다.
        double sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5);
        sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
        double sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5);
        sf = Math.pow(sf, sn) * Math.cos(slat1) / sn;
        double ro = Math.tan(Math.PI * 0.25 + olat * 0.5);
        ro = re * sf / Math.pow(ro, sn);

        // 변환 대상 위도에서 투영면 기준점까지의 거리와 기준 경도 대비 각도를 구한다.
        double ra = Math.tan(Math.PI * 0.25 + latitude * degrad * 0.5);
        ra = re * sf / Math.pow(ra, sn);
        double theta = longitude * degrad - olon;
        // 경도 차이를 -PI ~ PI 범위로 정규화해 날짜변경선 근처에서도 같은 방식으로 계산한다.
        if (theta > Math.PI) {
            theta -= 2.0 * Math.PI;
        }
        if (theta < -Math.PI) {
            theta += 2.0 * Math.PI;
        }
        theta *= sn;

        // 기상청 격자는 정수 좌표를 사용하므로 0.5를 더한 뒤 내림해 반올림 효과를 낸다.
        int nx = (int) Math.floor(ra * Math.sin(theta) + XO + 0.5);
        int ny = (int) Math.floor(ro - ra * Math.cos(theta) + YO + 0.5);
        return new Grid(nx, ny);
    }

    public record Grid(int nx, int ny) {
    }
}
