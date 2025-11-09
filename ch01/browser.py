import socket
import ssl

class URL:
    def __init__ (self, url):
        self.scheme, url = url.split("://", 1)  # ://가 처음 1번째를 기준으로 분할하고 http 제외한 부분만 url에 남김
        assert self.scheme in ["http", "https"]  # scheme이 http 또는 https임을 보장

        # http 또는 https의 경우 (기본 포트 사용)
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:  # url에 /가 없으면 추가
            url = url + "/"
        self.host, url = url.split("/", 1)  # 호스트만 분리
        self.path = "/" + url  # url에 /(경로) 추가

        # host에 포트값 포함일 경우
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request (self):
        s = socket.socket(  # 소켓 생성
            family = socket.AF_INET,  # address family
            type = socket.SOCK_STREAM,  # 임의의 양의 데이터를 전송
            proto = socket.IPPROTO_TCP,  # TCP Protocol 사용
        )
        s.connect((self.host, self.port))  # host 주소와 연결할 포트 설정, 서버와 연결 완료

        if self.scheme == "https":
            ctx = ssl.create_default_context()  # 컨텍스트 ctx 생성
            s = ctx.wrap_socket(s, server_hostname=self.host)  # ctx로 소켓을 감싸고 새 소켓 변수를 다시 할당 (hostname의 일치여부 확인)

        # 서버에 요청 전달
        request = "GET {} HTTP/1.0\r\n".format(self.path)  # 줄바꿈으로 \r\n 사용 (HTTP의 줄구분자가 \r\n)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"  # 텔넷 테스트처럼 \r\n 두 번 보내서 END 알려야 함
        s.send(request.encode("utf8"))  # 요청 전달, encode는 텍스트 투 바이트 / decode는 바이트 투 텍스트

        # 서버의 응답 읽기
        response = s.makefile("r", encoding ="utf8", newline="\r\n")  # 소켓을 읽는 makefile 메서드, utf8 인코딩을 사용하는 문자열로 변환
        statusline = response.readline()  # 상태 저장
        version, status, explanation = statusline.split(" ", 2)
        response_headers= {}  # 헤더 저장 (딕셔너리)
        while True:
            line = response.readline()  # 한 줄씩 읽기
            if line == "\r\n": break  # 헤더만 읽기
            header, value = line.split(":", 1)  # 헤더이름 : 값 분리
            response_headers[header.casefold()] = value.strip()  # 헤더이름(소문자):밸류 저장

        # 중요 헤더 여부 확인 및 보장
        assert "transfer-encoding" not in response_headers  # 압축 알고리즘
        assert "content-encoding" not in response_headers  # 헤더 압축

        body = response.read()  # 남은 내용 전부 가져오기
        s.close()  # 소켓 종료
        
        return body  # 화면에 출력할 값

def show(body):
    '''
    browser에 body 출력
    '''
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:  # <TAG>Contents</TAG> 중 Contents만 출력
            print(c, end="")

def load(url):
    '''
    웹페이지 로드
    '''
    body = url.request()
    show(body)


if __name__ == "__main__":
    '''
    CLI에서 스크립트를 실행했을 때만 파이썬 코드 실행
    '''
    import sys
    load(URL(sys.argv[1]))  # url 인자 전달

