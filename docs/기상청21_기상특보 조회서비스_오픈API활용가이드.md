# 기상청21_기상특보 조회서비스_오픈API활용가이드.docx

- Source format: `.docx`

기상청 기상특보 조회서비스

Open API 활용가이드

목 차

[1. 서비스 명세 [3](#_Toc26088835)](#_Toc26088835)

[**1.1 기상특보 조회서비스** [3](#_Toc26088836)](#_Toc26088836)

[가. API 서비스 개요 [3](#_Toc26088837)](#_Toc26088837)

[다. 상세기능내역 [5](#_Toc26088838)](#_Toc26088838)

[1) \[기상특보목록조회\] 상세기능명세 [5](#_Toc26088839)](#_Toc26088839)

[2) \[기상특보통보문조회\] 상세기능명세 [8](#_Toc26088840)](#_Toc26088840)

[3) \[기상정보목록조회\] 상세기능명세 [12](#_Toc26088841)](#_Toc26088841)

[4) \[기상정보문조회\] 상세기능명세 [15](#_Toc26088842)](#_Toc26088842)

[5) \[기상속보목록조회\] 상세기능명세 [18](#_Toc26088843)](#_Toc26088843)

[6) \[기상속보조회\] 상세기능명세 [21](#_Toc26088844)](#_Toc26088844)

[7) \[기상예비특보목록조회\] 상세기능명세 [24](#_Toc26088845)](#_Toc26088845)

[8) \[기상예비특보조회\] 상세기능명세 [27](#_Toc26088846)](#_Toc26088846)

[9) \[특보코드조회\] 상세기능명세 [30](#_Toc26088847)](#_Toc26088847)

[10) \[특보현황조회\] 상세기능명세 [34](#_Toc26088848)](#_Toc26088848)

[\# 첨부. 지점코드 [37](#_Toc29825350)](#_Toc29825350)

[\# 첨부. Open API 에러 코드 정리 [38](#_Toc29480709)](#_Toc29480709)

<span id="_Toc26088835" class="anchor"></span>**1. 서비스 명세**

<span id="_Toc26088836" class="anchor"></span>**1.1 기상특보 조회서비스**

<span id="_Toc26088837" class="anchor"></span>가. API 서비스 개요

<table>
<colgroup>
<col style="width: 19%" />
<col style="width: 19%" />
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
</colgroup>
<thead>
<tr class="header">
<th rowspan="3"><strong>API 서비스 정보</strong></th>
<th><strong>API명(영문)</strong></th>
<th colspan="3">WthrWrnInfoService</th>
</tr>
<tr class="odd">
<th><strong>API명(국문)</strong></th>
<th colspan="3">기상특보 조회서비스</th>
</tr>
<tr class="header">
<th><strong>API 설명</strong></th>
<th colspan="3">기상특보목록, 기상특보통보문, 기상정보목록, 기상정보문, 기상속보목록, 기상속보, 기상예비특보목록, 기상예비특보, 특보코드, 특보현황 정보를 조회하는 서비스</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td rowspan="5"><p><strong>API 서비스</strong></p>
<p><strong>보안적용</strong></p>
<p><strong>기술 수준</strong></p></td>
<td><strong>서비스 인증/권한</strong></td>
<td colspan="3"><p>[O] ServiceKey [ ] 인증서 (GPKI/NPKI)</p>
<p>[ ] Basic (ID/PW) [ ] 없음</p></td>
</tr>
<tr class="even">
<td><p><strong>메시지 레벨</strong></p>
<p><strong>암호화</strong></p></td>
<td colspan="3">[ ] 전자서명 [ ] 암호화 [O] 없음</td>
</tr>
<tr class="odd">
<td><strong>전송 레벨 암호화</strong></td>
<td colspan="3">[ ] SSL [O] 없음</td>
</tr>
<tr class="even">
<td><strong>인터페이스 표준</strong></td>
<td colspan="3"><p>[ ] SOAP 1.2</p>
<p>(RPC-Encoded, Document Literal, Document Literal Wrapped)</p>
<p>[O] REST (GET)</p>
<p>[ ] RSS 1.0 [ ] RSS 2.0 [ ] Atom 1.0 [ ] 기타</p></td>
</tr>
<tr class="odd">
<td><p><strong>교환 데이터 표준</strong></p>
<p><strong>(중복선택가능)</strong></p></td>
<td colspan="3">[O] XML [O] JSON [ ] MIME [ ] MTOM</td>
</tr>
<tr class="even">
<td rowspan="7"><p><strong>API 서비스</strong></p>
<p><strong>배포정보</strong></p></td>
<td><strong>서비스 URL</strong></td>
<td colspan="3">http://apis.data.go.kr/1360000/WthrWrnInfoService</td>
</tr>
<tr class="odd">
<td><p><strong>서비스 명세 URL</strong></p>
<p><strong>(WSDL 또는 WADL)</strong></p></td>
<td colspan="3">N/A</td>
</tr>
<tr class="even">
<td><strong>서비스 버전</strong></td>
<td colspan="3">1.0</td>
</tr>
<tr class="odd">
<td><strong>서비스 시작일</strong></td>
<td>2019-12-20</td>
<td><strong>서비스 배포일</strong></td>
<td>2019-12-20</td>
</tr>
<tr class="even">
<td><strong>서비스 이력</strong></td>
<td colspan="3">2019-12-20 : 서비스 시작</td>
</tr>
<tr class="odd">
<td><strong>메시지 교환유형</strong></td>
<td colspan="3"><p>[O] Request-Response [ ] Publish-Subscribe</p>
<p>[ ] Fire-and-Forgot [ ] Notification</p></td>
</tr>
<tr class="even">
<td><strong>데이터 갱신주기</strong></td>
<td colspan="3">수시 (특보 발생/해제 시)</td>
</tr>
</tbody>
</table>

나. 상세기능 목록

| **번호** | **API명(국문)**     | **상세기능명(영문)** | **상세기능명(국문)** |
|----------|---------------------|----------------------|----------------------|
| 1        | 기상특보 조회서비스 | getWthrWrnList       | 기상특보목록조회     |
| 2        |                     | getWthrWrnMsg        | 기상특보통보문조회   |
| 3        |                     | getWthrInfoList      | 기상정보목록조회     |
| 4        |                     | getWthrInfo          | 기상정보문조회       |
| 5        |                     | getWthrBrkNewsList   | 기상속보목록조회     |
| 6        |                     | getWthrBrkNews       | 기상속보조회         |
| 7        |                     | getWthrPwnList       | 기상예비특보목록조회 |
| 8        |                     | getWthrPwn           | 기상예비특보조회     |
| 9        |                     | getPwnCd             | 특보코드조회         |
| 10       |                     | getPwnStatus         | 특보현황조회         |

<span id="_Toc26088838" class="anchor"></span>다. 상세기능내역

<span id="_Toc26088839" class="anchor"></span>1) \[기상특보목록조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 1                                                                                                                                                                                 | **상세기능 유형**      | 조회 (상세) |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상특보목록조회                                                                                                                                                                  |                        |             |
| **상세기능 설명**      | 기상특보목록 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 제목, 순번, 지점코드, 발표번호(월별), 발표시각(년월일시분)의 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrWrnList</u>                                                                                                           |                        |             |
| **최대 메시지 사이즈** | \[2289\] byte                                                                                                                                                                     |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                        | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>184</td>
<td><p>지점코드</p>
<p>*하단 지점코드 자료 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170601</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>title</td>
<td>제목</td>
<td>200</td>
<td>1</td>
<td>예제 참조</td>
<td>제목</td>
</tr>
<tr class="even">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>28</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>25</td>
<td>1</td>
<td>201706070730</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnList</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=184&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;title&gt;[특보] 제06-28호 : 2017.06.07.07:30 / 강풍주의보·풍랑주의보 해제 (*)&lt;/title&gt;</p>
<p>                &lt;tmFc&gt;201706070730&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;28&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088840" class="anchor"></span>2) \[기상특보통보문조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 2                                                                                                                                                                                                                                         | **상세기능 유형**      | 조회 (목록) |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상특보통보문조회                                                                                                                                                                                                                        |                        |             |
| **상세기능 설명**      | 기상특보 정보를 조회하기 위해 발표시각(FROM), 발표시각(TO), 지점코드(stnId)의 조회조건으로 지점코드, 발표시각, 발표번호, 특보발표코드, 제목, 해당구역, 발효시각,내용, 특보발효현황시각, 특보발효현황내용, 참고사항의 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrWrnMsg</u>                                                                                                                                                                    |                        |             |
| **최대 메시지 사이즈** | \[5311\] byte                                                                                                                                                                                                                             |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                                                                                | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170601</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 00시 00분</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 23시 59분</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td>발표시각</td>
<td>12</td>
<td>1</td>
<td>201706070700</td>
<td>발표시각</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>27</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>warFc</td>
<td>특보발표코드</td>
<td>2</td>
<td>1</td>
<td>1</td>
<td>발표 (1로 고정)</td>
</tr>
<tr class="odd">
<td>t1</td>
<td>제목</td>
<td>500</td>
<td>1</td>
<td>예제 참조</td>
<td>제목</td>
</tr>
<tr class="even">
<td>t2</td>
<td>해당구역</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>해당구역</td>
</tr>
<tr class="odd">
<td>t3</td>
<td>발효시각</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>발효시각</td>
</tr>
<tr class="even">
<td>t4</td>
<td>내용</td>
<td>2000</td>
<td>1</td>
<td>예제 참조.</td>
<td>내용</td>
</tr>
<tr class="odd">
<td>t5</td>
<td>특보발효현황시각</td>
<td>12</td>
<td>1</td>
<td>201706070900</td>
<td>특보발효현황시각</td>
</tr>
<tr class="even">
<td>t6</td>
<td>특보발효현황내용</td>
<td>4000</td>
<td>1</td>
<td>예제 참조.</td>
<td>특보발효현황내용</td>
</tr>
<tr class="odd">
<td>t7</td>
<td>예비특보</td>
<td>4000</td>
<td>1</td>
<td>예제 참조</td>
<td>예비특보 발효현황</td>
</tr>
<tr class="even">
<td>other</td>
<td>참고사항</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>참고사항</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnMsg</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;fromTmFc=20170607&amp;toTmFc=20170607&amp;stnId=125</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;other&gt;o 없음&lt;/other&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;t1&gt;강풍주의보·풍랑주의보 발표&lt;/t1&gt;</p>
<p>                &lt;t2&gt;(1) 강풍주의보 발표 : 울릉도.독도</p>
<p>(2) 풍랑주의보 발표 : 동해중부먼바다, 동해남부먼바다&lt;/t2&gt;</p>
<p>                &lt;t3&gt;(1) 강풍주의보 발표 : 2017년 06월 07일 09시 00분</p>
<p>(2) 풍랑주의보 발표 : 2017년 06월 07일 09시 00분&lt;/t3&gt;</p>
<p>                &lt;t4&gt;(1) 강풍주의보 발표</p>
<p>o 해제 예고: 7일 밤</p>
<p>(2) 풍랑주의보 발표</p>
<p>o 해제 예고: 8일 새벽&lt;/t4&gt;</p>
<p>                &lt;t5&gt;201706070900&lt;/t5&gt;</p>
<p>                &lt;t6&gt;o 강풍주의보 : 울릉도.독도, 전라남도(거문도.초도)</p>
<p>o 풍랑주의보 : 남해서부동쪽먼바다, 남해동부먼바다, 동해중부먼바다, 동해남부먼바다&lt;/t6&gt;</p>
<p>                &lt;t7&gt;(1) 풍랑 예비특보</p>
<p>o 06월 07일 아침 : 동해중부앞바다, 동해남부앞바다(경북북부앞바다, 경북남부앞바다)&lt;/t7&gt;</p>
<p>                &lt;tmFc&gt;201706070700&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;27&lt;/tmSeq&gt;</p>
<p>                &lt;warFc&gt;1&lt;/warFc&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088841" class="anchor"></span>3) \[기상정보목록조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 3                                                                                                                                                                                 | **상세기능 유형**      | 조회 (상세) |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상정보목록조회                                                                                                                                                                  |                        |             |
| **상세기능 설명**      | 기상정보목록 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 제목, 순번, 지점코드, 발표번호(월별), 발표시각(년월일시분)의 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrInfoList</u>                                                                                                          |                        |             |
| **최대 메시지 사이즈** | \[1959\] byte                                                                                                                                                                     |                        |             |
| **평균 응답 시간**     | \[150\] ms                                                                                                                                                                        | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td>지점코드 별첨</td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>title</td>
<td>제목</td>
<td>200</td>
<td>1</td>
<td>예제 참조</td>
<td>제목</td>
</tr>
<tr class="even">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>184</td>
<td>지점번호</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>47</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>25</td>
<td>1</td>
<td>201706070410</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrInfoList</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=108&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;title&gt;[정보] 제06-13호 : 2017.06.07.04:10&lt;/title&gt;</p>
<p>                &lt;tmFc&gt;201706070410&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;13&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088842" class="anchor"></span>4) \[기상정보문조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 4                                                                                                                                                                                     | **상세기능 유형**      | 조회 (상세) |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상정보문조회                                                                                                                                                                        |                        |             |
| **상세기능 설명**      | 기상정보 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 지점코드, 발표시각(년월일시분), 발표번호(월별), 기상정보 내용의 정보를 조회하기 위한 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrInfo</u>                                                                                                                  |                        |             |
| **최대 메시지 사이즈** | \[3418\] byte                                                                                                                                                                         |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                            | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td><p>지점코드</p>
<p>*하단 지점코드 표 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 00시 00분</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 23시 59분</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td>발표시각</td>
<td>12</td>
<td>1</td>
<td>201706070410</td>
<td>발표시각(년월일시분)</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>13</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>t1</td>
<td>기상정보</td>
<td>4000</td>
<td>1</td>
<td>예제 참조</td>
<td>기상정보</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrInfo</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=108&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;t1&gt;&lt; 기상 현황과 전망 &gt; o 현재, 전국이 흐리고 비가 내리고 있습니다. * 주요지점 누적 강수량 현황(6일부터 7일 04시 현재, 단위 : mm) - [중부지방] 서울 22.5 춘천 22.3 인천 22.1 대전 11.0 청주 7.6 - [남부지방] 완도 64.4 고흥 64.0 보성 46.5 진도 36.0 여수 28.8 광주 6.0 - [제주도] 서귀포 143.7 진달래밭 117.0 o 오늘은 서해상에서 동진하는 저기압의 영향을 받은 후 벗어나겠습니다. 전국이 대체로 흐리고 비가 오다가 오전에 남서쪽부터 차차 그치기 시작하여 오후에 대부분 그치겠으나, 강원영서는 저녁까지 이어지는 곳이 있겠습니다. * 예상 강수량(7일 저녁까지) - 전국(제주도 제외), 북한(8일까지) : 5mm 내외 * 예상 강수량은 05시 예보에서 변경될 수 있습니다. o 내일(8일)은 남해상에 위치한 고기압의 영향을 받겠습니다. 전국이 대체로 맑겠습니다. o 모레(9일)는 남해상에서 동진하는 고기압의 가장자리에 들겠습니다. 전국에 가끔 구름이 많겠으나, 강원영서북부는 북쪽을 지나는 약한 기압골의 영향으로 밤에 비가 오는 곳이 있겠습니다. &lt; 기온 전망 &gt; o 오늘 낮 기온은 평년보다 낮겠으나, 내일(8일)부터 맑은 날씨를 보이면서 기온이 올라 평년과 비슷하거나 조금 높은 분포를 보이겠습니다. &lt; 안개 전망 &gt; o 오늘 아침까지 해안과 일부 내륙을 중심으로 안개가 짙게 끼는 곳이 있겠으니, 교통안전에 유의하기 바랍니다. &lt; 강풍 전망 &gt; o 오늘까지 해안과 일부 내륙, 내일(8일)과 모레(9일)는 강원산지에 바람이 강하게 부는 곳이 있겠으니, 시설물 관리에 유의하기 바랍니다. &lt; 해상 전망 &gt; o 현재, 서해상과 제주도해상, 남해상에 풍랑특보가 발효된 가운데, 오늘은 전해상에 바람이 강하게 불고, 물결이 높게 일겠으니, 앞으로 발표되는 기상정보를 참고하기 바랍니다. o 오늘은 전해상, 내일(8일)과 모레(9일)는 서해상과 남해상에 안개가 끼는 곳이 있겠으니, 항해나 조업하는 선박은 유의하기 바랍니다.&lt;/t1&gt;</p>
<p>                &lt;tmFc&gt;201706070410&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;13&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088843" class="anchor"></span>5) \[기상속보목록조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 5                                                                                                                                                                               | **상세기능 유형**      | 조회 (상세) |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상속보목록조회                                                                                                                                                                |                        |             |
| **상세기능 설명**      | 기상속보목록 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 제목, 순번, 지점코드, 발표번호(월별), 발표시각(년월일시분) 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrBrkNewsList</u>                                                                                                     |                        |             |
| **최대 메시지 사이즈** | \[1950\] byte                                                                                                                                                                   |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                      | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td><p>지점코드</p>
<p>*하단 지점코드 표 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>title</td>
<td>제목</td>
<td>200</td>
<td>1</td>
<td>예제 참조</td>
<td>제목</td>
</tr>
<tr class="even">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>39</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>25</td>
<td>1</td>
<td>201706070910</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrBrkNewsList</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;</u><u>stnId=108&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;title&gt;[속보] 제10-39호 : 2017.06.07.09:10&lt;/title&gt;</p>
<p>                &lt;tmFc&gt;201706070910&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;39&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088844" class="anchor"></span>6) \[기상속보조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 6                                                                                                                                                                                                 | **상세기능 유형**      | 조회 (상세) |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상속보조회                                                                                                                                                                                      |                        |             |
| **상세기능 설명**      | 기상속보 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 지점코드, 발표시간(년월일시분), 발표번호, 입력시간(년월일시분초), 참조번호, 내용 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrBrkNews</u>                                                                                                                           |                        |             |
| **최대 메시지 사이즈** | \[7894\] byte                                                                                                                                                                                     |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                                        | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td><p>지점코드</p>
<p>*하단 지점코드 표 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>1</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 시간단위로 생성).</p>
<p>☞ 미입력시 현재일자 00시 00분</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>1</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 23시 59분</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>3</td>
<td>1</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td>발표시간</td>
<td>21</td>
<td>1</td>
<td>201706070910</td>
<td>발표시간</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호</td>
<td>3</td>
<td>0</td>
<td>39</td>
<td>발표번호</td>
</tr>
<tr class="even">
<td>cnt</td>
<td>참조번호</td>
<td>3</td>
<td>0</td>
<td>4</td>
<td>참조번호</td>
</tr>
<tr class="odd">
<td>ann</td>
<td>내용</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>내용</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrBrkNews</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=108&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;ann&gt;&lt;안개 현황 및 전망&gt; o 현재, 내륙을 중심으로 안개가 짙게 낀 곳이 있음 * 주요 지점별 가시거리(09시 현재, 단위: m) [시정계] 공주 540 곡성 290 화순 300 주천(진안) 240 * 시정계 자료는 목측 관측자료와 다소 차이가 있을 수 있음 o 아침까지 안개가 짙게 끼는 곳이 있겠으니, 교통안전에 유의바람&lt;/ann&gt;</p>
<p>                &lt;cnt&gt;4&lt;/cnt&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;tmFc&gt;201706070910&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;39&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088845" class="anchor"></span>7) \[기상예비특보목록조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 7                                                                                                                                                                                   | **상세기능 유형**      | 조회 (목록) |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상예비특보목록조회                                                                                                                                                                |                        |             |
| **상세기능 설명**      | 기상예비특보목록 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 제목, 순번, 지점코드, 발표번호(월별), 발표시각(년월일시분) 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrPwnList</u>                                                                                                             |                        |             |
| **최대 메시지 사이즈** | \[1998\] byte                                                                                                                                                                       |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                          | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>156</td>
<td><p>지점코드</p>
<p>*하단 지점코드 표 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 시간단위로 생성)</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 시간단위로 생성)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>title</td>
<td>제목</td>
<td>200</td>
<td>1</td>
<td>예제 참조</td>
<td>제목</td>
</tr>
<tr class="even">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>7</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>25</td>
<td>1</td>
<td>201706070730</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrPwnList</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=108&amp;fromTmFc=20170607&amp;toTmFc=20170607</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;title&gt;[예비] 제06-7호 : 2017.06.07.07:30&lt;/title&gt;</p>
<p>                &lt;tmFc&gt;201706070730&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;7&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088846" class="anchor"></span>8) \[기상예비특보조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 8                                                                                                                                                                                                                       | **상세기능 유형**      | 조회 (상세) |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 기상예비특보조회                                                                                                                                                                                                        |                        |             |
| **상세기능 설명**      | 기상예비특보 정보를 조회하기 위해 발표시각(From), 발표시각(To), 지점코드(stnId)의 조회 조건으로 지점코드, 발표시간(년월일시분), 발표번호, 입력시간(년월일시분초), 참조번호, 예비특보현황, 참고사항 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getWthrPwn</u>                                                                                                                                                     |                        |             |
| **최대 메시지 사이즈** | \[8557\] byte                                                                                                                                                                                                           |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                                                              | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td><p>지점코드</p>
<p>*하단 지점코드 표 참조</p></td>
</tr>
<tr class="even">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>1</td>
<td>20170606</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 00시 00분</p></td>
</tr>
<tr class="odd">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>1</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 23시 59분</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점코드</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td>지점코드</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시간</p>
<p>(년월일시분)</p></td>
<td>21</td>
<td>1</td>
<td>201706062300</td>
<td><p>발표시간</p>
<p>(년월일시분)</p></td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호</td>
<td>4</td>
<td>0</td>
<td>6</td>
<td>발표번호</td>
</tr>
<tr class="even">
<td><del>cnt</del></td>
<td><del>참조번호</del></td>
<td><del>3</del></td>
<td><del>0</del></td>
<td><del>4</del></td>
<td><del>참조번호</del></td>
</tr>
<tr class="odd">
<td>pwn</td>
<td>예비특보현황</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>예비특보현황</td>
</tr>
<tr class="even">
<td>rem</td>
<td>참고사항</td>
<td>1000</td>
<td>0</td>
<td>없음</td>
<td>참고사항</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

\*cnt 참조번호 삭제(2020.11.27.)

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrPwn</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;stnId=108&amp;fromTmFc=20150101&amp;toTmFc=20151013</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;pwn&gt;(1) 강풍 예비특보 o 06월 07일 아침 : 울릉도.독도</p>
<p>(2) 풍랑 예비특보 o 06월 07일 아침 : 동해중부전해상, 동해남부먼바다, 동 해남부앞바다(경북북부앞바다, 경북남부앞바다)&lt;/pwn&gt;</p>
<p>                &lt;rem&gt;o 당초 오늘(6일) 밤으로 예고되었던 경기해안, 충남해안, 경남남해안의 강 풍 예비특보와 서해중부앞바다, 남해동부앞바다(경남중부남해앞바다)의 풍 랑 예비특보는 발표가능성이 적어졌음을 알려드립니다.&lt;/rem&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;tmFc&gt;201706062300&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;6&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088847" class="anchor"></span>9) \[특보코드조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 9                                                                                                                                                                                                                                                                                                                       | **상세기능 유형**      | 조회 (상세) |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 특보코드조회                                                                                                                                                                                                                                                                                                            |                        |             |
| **상세기능 설명**      | 특보구역 코드를 기반으로 해당 구역에 내려진 특보를 조회하기 위해 발표시각(From), 발표시각(To), 특보구역코드, 특보종류의 조회 조건으로 지점번호, 발표시각(년월일시분), 발표번호(월별), 특보구역코드, 구역명, 특보종류, 특보강도, 특보발표코드, 발효시각, 발효해제시각, 전체특보해제시각, 취소구분의 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getPwnCd</u>                                                                                                                                                                                                                                                       |                        |             |
| **최대 메시지 사이즈** | \[3129\] byte                                                                                                                                                                                                                                                                                                           |                        |             |
| **평균 응답 시간**     | \[150\] ms                                                                                                                                                                                                                                                                                                              | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
<tr class="odd">
<td>fromTmFc</td>
<td>발표시각(From)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 00시 00분</p></td>
</tr>
<tr class="even">
<td>toTmFc</td>
<td>발표시각(To)</td>
<td>8</td>
<td>0</td>
<td>20170607</td>
<td><p>시간(년월일)</p>
<p>(데이터 생성주기 : 시간단위로 생성)</p>
<p>☞ 미입력시 현재일자 23시 59분</p></td>
</tr>
<tr class="odd">
<td>areaCode</td>
<td>특보구역코드</td>
<td>10</td>
<td>0</td>
<td>L1070100</td>
<td><p>특보구역코드</p>
<p>*별첨 엑셀 자료 참조</p></td>
</tr>
<tr class="even">
<td>warningType</td>
<td>특보종류</td>
<td>2</td>
<td>0</td>
<td>4</td>
<td><p>1-강풍, 2-호우,</p>
<p>3-한파, 4-건조,</p>
<p>5-폭풍해일, 6-풍랑,</p>
<p>7-태풍, 8-대설,</p>
<p>9-황사, 12-폭염</p></td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점번호</td>
<td>5</td>
<td>0</td>
<td>108</td>
<td>지점번호</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>stnId</td>
<td>지점번호</td>
<td>5</td>
<td>1</td>
<td>108</td>
<td>지점번호</td>
</tr>
<tr class="even">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>21</td>
<td>1</td>
<td>201706070900</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
<tr class="odd">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>28</td>
<td>발표번호(월별)</td>
</tr>
<tr class="even">
<td>areaCode</td>
<td>특보구역코드</td>
<td>10</td>
<td>1</td>
<td>S1322200</td>
<td><p>특보구역코드</p>
<p>* 별첨 엑셀 자료 참조</p></td>
</tr>
<tr class="odd">
<td>areaName</td>
<td>구역명</td>
<td>50</td>
<td>1</td>
<td>예제 참조</td>
<td>구역명</td>
</tr>
<tr class="even">
<td>warnVar</td>
<td>특보종류</td>
<td>2</td>
<td>0</td>
<td>4</td>
<td><p>1-강풍, 2-호우, 3-한파, 4-건조,</p>
<p>5-폭풍해일, 6-풍랑,7-태풍,</p>
<p>8-대설, 9-황사, 12-폭염</p></td>
</tr>
<tr class="odd">
<td>warnStress</td>
<td>특보강도</td>
<td>1</td>
<td>0</td>
<td>0</td>
<td>0-주의보,1-경보</td>
</tr>
<tr class="even">
<td>command</td>
<td>특보발표코드</td>
<td>1</td>
<td>0</td>
<td>1</td>
<td><p>1-발표, 2-해제,</p>
<p>3-연장, 6-정정,</p>
<p>7-변경발표,</p>
<p>8-변경해제</p></td>
</tr>
<tr class="odd">
<td>startTime</td>
<td>발표시 발효시각</td>
<td>21</td>
<td>1</td>
<td>201706070730</td>
<td>발표발효시각(특보발표시에만 제공)</td>
</tr>
<tr class="even">
<td>endTime</td>
<td>해제시 발효시각</td>
<td>21</td>
<td>1</td>
<td>201706070730</td>
<td>해제발효시각(특보해제시에만 제공)</td>
</tr>
<tr class="odd">
<td>allEndTime</td>
<td>전체특보해제시각</td>
<td>21</td>
<td>1</td>
<td>201706070730</td>
<td>전체특보해제시각</td>
</tr>
<tr class="even">
<td>cancel</td>
<td>취소구분</td>
<td>1</td>
<td>0</td>
<td>0</td>
<td><p>취소구분</p>
<p>(0–정상, 1-취소된 특보)</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnCd</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1<br />
&amp;fromTmFc=20170607&amp;toTmFc=20170607&amp;areaCode=S1322200&amp;warninType=6</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;allEndTime&gt;201706070900&lt;/allEndTime&gt;</p>
<p>                &lt;areaCode&gt;S1322200&lt;/areaCode&gt;</p>
<p>                &lt;areaName&gt;남해서부동쪽먼바다&lt;/areaName&gt;</p>
<p>                &lt;cancel&gt;0&lt;/cancel&gt;</p>
<p>                &lt;command&gt;2&lt;/command&gt;</p>
<p>                &lt;endTime&gt;201706070900&lt;/endTime&gt;</p>
<p>                &lt;stnId&gt;108&lt;/stnId&gt;</p>
<p>                &lt;tmFc&gt;201706070730&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;28&lt;/tmSeq&gt;</p>
<p>                &lt;warnStress&gt;0&lt;/warnStress&gt;</p>
<p>                &lt;warnVar&gt;6&lt;/warnVar&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc26088848" class="anchor"></span>10) \[특보현황조회\] 상세기능명세

a\) 상세기능정보

| **상세기능 번호**      | 10                                                                                                                                                                                     | **상세기능 유형**      | 조회 (상세) |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|-------------|
| **상세기능명(국문)**   | 특보현황조회                                                                                                                                                                           |                        |             |
| **상세기능 설명**      | 최근 7일 이내의 특보현황(특보, 예비특보) 정보를 조회하여 발표시각(년월일시분), 발표번호(월별), 특보발효현황 시각, 특보발효현황 내용, 예비특보발효현황, 참고사항의 정보를 조회하는 기능 |                        |             |
| **Call Back URL**      | http://apis.data.go.kr/1360000/<u>WthrWrnInfoService/getPwnStatus</u>                                                                                                                  |                        |             |
| **최대 메시지 사이즈** | \[1601\] byte                                                                                                                                                                          |                        |             |
| **평균 응답 시간**     | \[100\] ms                                                                                                                                                                             | **초당 최대 트랙잭션** | \[30\] tps  |

b\) 요청 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 26%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>serviceKey</td>
<td>인증키</td>
<td>100</td>
<td>1</td>
<td><p>인증키</p>
<p>(URL Encode)</p></td>
<td>공공데이터포털에서 발급받은 인증키</td>
</tr>
<tr class="even">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>10</td>
<td><p>한 페이지 결과 수</p>
<p>Default: 10</p></td>
</tr>
<tr class="odd">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>페이지 번호</p>
<p>Default: 1</p></td>
</tr>
<tr class="even">
<td>dataType</td>
<td>응답자료형식</td>
<td>4</td>
<td>0</td>
<td>XML</td>
<td><p>요청자료형식(XML/JSON)</p>
<p>Default: XML</p></td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

c\) 응답 메시지 명세

<table>
<colgroup>
<col style="width: 16%" />
<col style="width: 16%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 19%" />
<col style="width: 24%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>항목명(영문)</strong></th>
<th><strong>항목명(국문)</strong></th>
<th><strong>항목크기</strong></th>
<th><strong>항목구분</strong></th>
<th><strong>샘플데이터</strong></th>
<th><strong>항목설명</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>numOfRows</td>
<td>한 페이지 결과 수</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td><p>한 페이지당 표출</p>
<p>데이터 수</p></td>
</tr>
<tr class="even">
<td>pageNo</td>
<td>페이지 번호</td>
<td>4</td>
<td>1</td>
<td>1</td>
<td>페이지 수</td>
</tr>
<tr class="odd">
<td>totalCount</td>
<td>데이터 총 개수</td>
<td>10</td>
<td>1</td>
<td>1</td>
<td>데이터 총 개수</td>
</tr>
<tr class="even">
<td>resultCode</td>
<td>응답메시지 코드</td>
<td>2</td>
<td>1</td>
<td>00</td>
<td>응답 메시지코드</td>
</tr>
<tr class="odd">
<td>resultMsg</td>
<td>응답메시지 내용</td>
<td>100</td>
<td>1</td>
<td>NORMAL SERVICE</td>
<td>응답 메시지 설명</td>
</tr>
<tr class="even">
<td>dataType</td>
<td>데이터 타입</td>
<td>4</td>
<td>1</td>
<td>XML</td>
<td>응답자료형식 (XML/JSON)</td>
</tr>
<tr class="odd">
<td>tmFc</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
<td>date</td>
<td>1</td>
<td>201706070900</td>
<td><p>발표시각</p>
<p>(년월일시분)</p></td>
</tr>
<tr class="even">
<td>tmSeq</td>
<td>발표번호(월별)</td>
<td>4</td>
<td>0</td>
<td>41</td>
<td>발표번호(월별)</td>
</tr>
<tr class="odd">
<td>tmEf</td>
<td>특보발효현황 시각</td>
<td>12</td>
<td>1</td>
<td>201706070730</td>
<td>특보발효현황 시각</td>
</tr>
<tr class="even">
<td>t6</td>
<td>특보발효현황 내용</td>
<td>4000</td>
<td>1</td>
<td>예제 참조</td>
<td>특보발효현황 내용</td>
</tr>
<tr class="odd">
<td>t7</td>
<td>예비특보 발효현황</td>
<td>2000</td>
<td>1</td>
<td>예제 참조</td>
<td>예비특보 발효현황</td>
</tr>
<tr class="even">
<td>other</td>
<td>참고사항</td>
<td>2000</td>
<td>1</td>
<td>없음</td>
<td>참고사항</td>
</tr>
</tbody>
</table>

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n), 코드표별첨

d\) 요청/응답 메시지 예제

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>요청메시지</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><u>http://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnStatus</u><br />
<u>?serviceKey=인증키&amp;numOfRows=10&amp;pageNo=1</u></td>
</tr>
<tr class="even">
<td><strong>응답메시지</strong></td>
</tr>
<tr class="odd">
<td><p>&lt;?xml version="1.0" encoding="UTF-8"?&gt;</p>
<p>&lt;response&gt;</p>
<p>    &lt;header&gt;</p>
<p>        &lt;resultCode&gt;0&lt;/resultCode&gt;</p>
<p>        &lt;resultMsg&gt;NORMAL_SERVICE&lt;/resultMsg&gt;</p>
<p>    &lt;/header&gt;</p>
<p>    &lt;body&gt;</p>
<p>        &lt;dataType&gt;XML&lt;/dataType&gt;</p>
<p>        &lt;items&gt;</p>
<p>            &lt;item&gt;</p>
<p>                &lt;other&gt;o 없음&lt;/other&gt;</p>
<p>                &lt;t6&gt;o 강풍주의보 : 울릉도.독도</p>
<p>o 풍랑주의보 : 남해동부먼바다, 동해중부먼바다, 동해남부먼바다&lt;/t6&gt;</p>
<p>                &lt;t7&gt;(1) 풍랑 예비특보</p>
<p>o 06월 07일 아침 : 동해중부앞바다, 동해남부앞바다(경북북부앞바다, 경북 남부앞바다)&lt;/t7&gt;</p>
<p>                &lt;tmEf&gt;201706070900&lt;/tmEf&gt;</p>
<p>                &lt;tmFc&gt;201706070730&lt;/tmFc&gt;</p>
<p>                &lt;tmSeq&gt;28&lt;/tmSeq&gt;</p>
<p>            &lt;/item&gt;</p>
<p>        &lt;/items&gt;</p>
<p>        &lt;numOfRows&gt;10&lt;/numOfRows&gt;</p>
<p>        &lt;pageNo&gt;1&lt;/pageNo&gt;</p>
<p>        &lt;totalCount&gt;1&lt;/totalCount&gt;</p>
<p>    &lt;/body&gt;</p>
<p>&lt;/response&gt;</p></td>
</tr>
</tbody>
</table>

<span id="_Toc29825350" class="anchor"></span>

\# 첨부. 지점코드

| **stnId** | **지점 명** | **특보해당구역**     |
|-----------|-------------|----------------------|
| 108       | 서울        | 전국                 |
| 109       | 서울        | 서울, 인천, 경기도   |
| 159       | 부산        | 부산. 울산. 경상남도 |
| 143       | 대구        | 대구. 경상북도       |
| 156       | 광주        | 광주. 전라남도       |
| 146       | 전주        | 전북자치도           |
| 133       | 대전        | 대전. 세종. 충청남도 |
| 131       | 청주        | 충청북도             |
| 105       | 강릉        | 강원도               |
| 184       | 제주        | 제주도               |

**\#특보구역코드#**

Excel 문서(기상청21_기상특보 조회서비스_오픈API활용가이드_특보구역코드안내.xlsx) 파일 참조

<span id="_Toc29480709" class="anchor"></span>\# 첨부. Open API 에러 코드 정리

| 에러코드 | 에러메세지                                       | 설명                                |
|----------|--------------------------------------------------|-------------------------------------|
| 0        | NORMAL_CODE                                      | 정상                                |
| 1        | APPLICATION_ERROR                                | 어플리케이션 에러                   |
| 2        | DB_ERROR                                         | 데이터베이스 에러                   |
| 3        | NODATA_ERROR                                     | 데이터없음 에러                     |
| 4        | HTTP_ERROR                                       | HTTP 에러                           |
| 5        | SERVICETIMEOUT_ERROR                             | 서비스 연결실패 에러                |
| 10       | INVALID_REQUEST_PARAMETER_ERROR                  | 잘못된 요청 파라메터 에러           |
| 11       | NO_MANDATORY_REQUEST_PARAMETERS_ERROR            | 필수요청 파라메터가 없음            |
| 12       | NO_OPENAPI_SERVICE_ERROR                         | 해당 오픈API서비스가 없거나 폐기됨  |
| 20       | SERVICE_ACCESS_DENIED_ERROR                      | 서비스 접근거부                     |
| 21       | TEMPORARILY_DISABLE_THE_SERVICEKEY_ERROR         | 일시적으로 사용할 수 없는 서비스 키 |
| 22       | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 서비스 요청제한횟수 초과에러        |
| 30       | SERVICE_KEY_IS_NOT_REGISTERED_ERROR              | 등록되지 않은 서비스키              |
| 31       | DEADLINE_HAS_EXPIRED_ERROR                       | 기한만료된 서비스키                 |
| 32       | UNREGISTERED_IP_ERROR                            | 등록되지 않은 IP                    |
| 33       | UNSIGNED_CALL_ERROR                              | 서명되지 않은 호출                  |
| 99       | UNKNOWN_ERROR                                    | 기타에러                            |
