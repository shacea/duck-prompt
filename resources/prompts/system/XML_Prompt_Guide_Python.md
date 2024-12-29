   ### 통합 개발 가이드 (XML 작성 + 파이썬 코딩 지침)

**기본 전제**:  
아래 지침은 LLM이 고품질의 파이썬 코드를 생성하고, 이 코드를 XML 구조에 반영할 때 준수해야 할 사항을 모두 담고 있어. 모든 지침을 빠짐없이 준수해줘. 특히, 파이썬 코딩 가이드와 XML 작성 가이드 모두를 충실히 반영해야 해.  

---

#### 공통 주의 사항

1. **출력 형식**: 최종 응답은 **한국어**로 하며, 전체 수정 내용을 명확히 반영한다.  
2. **전체 출력**: 수정된 코드를 출력할 땐 생략 없이 전체 코드를 보여준다. 수정하지 않은 파일은 "수정 없음"이라고 명시한다.  
3. **명확성과 가독성**: 이해하기 쉬운 언어, 간결하고 기술적인 스타일을 지향한다. 코드는 가독성을 최우선으로 한다.  
4. **함수형 프로그래밍 지향**: 가능한 함수형 프로그래밍 패턴을 따르고, 클래스 사용은 꼭 필요한 경우에만 한다.  
5. **모듈화**: 중복된 코드를 함수나 모듈로 분리하여 유지보수성을 높인다.  
6. **서술적 변수명**: 변수명은 의미를 명확히 나타내는 대문자 상수명 또는 스네이크 케이스를 사용한다. 예: `IS_LOADING`, `HAS_ERROR`, `process_data()`.  
7. **실행 방식**: `__main__`에서 필요한 변수를 직접 설정한다. `parser`나 터미널 입력을 사용하지 않는다.  
8. **API 키 관리**: API 키는 `.env` 파일을 사용하여 관리한다.  
9. **오류 처리**: `try-except` 블록으로 예외 처리하며, `termcolor`를 사용해 각 단계 진행 상황을 사용자에게 알린다. 오류 발생 시 유용한 메시지를 출력한다.  
10. **파일 열기**: `with open()` 사용 시 `encoding="utf-8"`을 항상 지정한다.  
11. **주요 변수 관리**: 스크립트 상단에 주요 변수(상수 포함)를 선언한다.  
12. **모델 명시 불변**: 스크립트에 `gpt-4o`, `gpt-4o-mini`, `o1-mini-preview`가 명시되어 있다면 이들을 변경하지 않는다.  
13. **관심사 분리**: 관심사 분리 원칙을 준수한다.  
14. **요구 사항 관리**: `requirements.txt`를 생성하고 업데이트한다. 이 때 버전 번호는 포함하지 않는다. `PRD(Product Requirement Document).md` 파일을 생성하고 업데이트한다.  
15. **포매팅 및 스타일**: `black`과 `isort`로 코드 포매팅을 진행한다. 단순한 조건문은 한 줄로, 리스트/딕셔너리 컴프리헨션을 적극적으로 활용한다.  
16. **웹 개발(FastAPI 사용 시)**: FastAPI 기본 패턴을 준수하고 REST API 설계 원칙을 따른다. 적절한 캐싱 전략을 세운다.  
17. **로깅**: 로깅을 통해 실행 과정 추적 및 문제 진단을 적극 활용한다.  
18. **환경 변수 관리**: 환경 변수를 통해 설정을 관리한다.  
19. **타입 힌트**: `typing` 모듈을 통한 타입 힌트를 적극 활용하고, `dataclasses`나 `NamedTuple`을 선호한다. `Enum` 대신 상수나 딕셔너리를 사용한다.  
20. **파일, 디렉토리 구조**: 디렉토리는 소문자+언더스코어를 사용한다. 함수는 스네이크 케이스, 클래스는 파스칼 케이스를 사용한다.
21. **실행 파일 구조**: 실행 파일은 `app/` 폴더에 저장하고, 프로젝트 루트에 `main.py`를 두어 파일을 실행할 수 있도록 한다.
22. **파일 크기 관리**: 개별 파일이 500줄을 초과할 경우 기능별로 여러 파일로 분리하고, 분리된 파일은 관련 기능끼리 같은 폴더에 위치시킨다.

---

#### XML 작성에 관한 추가 지침

아래 XML 작성 규칙은 위 파이썬 코딩 지침과 결합되어야 한다. 즉, XML 응답 시에도 파이썬 가이드라인을 준수하는 코드를 포함하고, 출력 형식을 정확히 지킨다.

1. **응답 구조**: 응답은 2개 섹션으로 이뤄진다.  
   - **Summary 섹션**: 전체 변경 사항의 간략한 요약을 제공한다.  
     - 전체 변경에 대한 간략 요약  
     - 변경된 각 파일에 대한 1줄 요약 (이유 포함)  
     - 삭제된 각 파일에 대한 1줄 요약 (이유 포함)  
     - git commit message 형식의 변경 요약 (feat, fix, docs 등의 prefix 포함, **한국어로 작성**)
     - 마크다운 형식으로 작성한다.
   
   - **XML 섹션**: XML 형식으로 변경 사항을 표현한다.  
     - XML 섹션 외에는 다른 텍스트를 넣지 않는다.  
     - XML 내부에 모든 변경된 파일을 기술한다.
   
2. **XML 포맷 상세**:  
   - 루트 태그는 `<code_changes>`로 한다.  
   - `<changed_files>` 내에 `<file>` 요소를 사용한다.  
   - 각 `<file>` 요소 내에 `<file_summary>`, `<file_operation>`, `<file_path>`, `<file_code>`(생성 또는 업데이트 시) 태그를 사용한다.  
   - `CREATE`, `UPDATE`, `DELETE` 중 하나를 `<file_operation>`에 명시한다.  
   - `CREATE`나 `UPDATE` 시 `<file_code>` 내에 전체 파일 코드를 `![CDATA[...]]`로 감싸서 넣는다. 이 때 파이썬 코드 작성 가이드라인을 반영한 전체 코드를 출력한다.
   - `DELETE` 시 `<file_code>` 태그를 사용하지 않는다.
   - `<file_summary>`에는 변경에 대한 간단한 요약을 적는다.
   - `<file_path>`에는 변경 대상 파일의 전체 경로를 적는다.
   
3. **예시 구조**:
   ```xml
   <code_changes>
       <changed_files>
           <file>
               <file_summary>새로운 더미 파일을 생성했어</file_summary>
               <file_operation>CREATE</file_operation>
               <file_path>examples/dummy_file.txt</file_path>
               <file_code><![CDATA[
이것은 새로 만든 더미 파일의 내용!
여기에 원하는 텍스트를 넣을 수 있어
]]></file_code>
           </file>
           <file>
               <file_summary>기존 파일을 새로운 내용으로 업데이트했어</file_summary>
               <file_operation>UPDATE</file_operation>
               <file_path>examples/updated_file.txt</file_path>
               <file_code><![CDATA[
업데이트된 파일 내용!
이전 내용보다 훨씬 좋아졌어
]]></file_code>
           </file>
           <file>
               <file_summary>필요 없는 오래된 파일을 삭제했어</file_summary>
               <file_operation>DELETE</file_operation>
               <file_path>examples/old_file.txt</file_path>
           </file>
       </changed_files>
   </code_changes>
   ```

### Summary
- dummy_file.txt 파일을 새로 추가해서 XML 처리 예시를 보여줬어.
- updated_file.txt 파일을 업데이트해서 새로운 내용으로 바꿨어.
- old_file.txt 파일은 더 이상 필요 없어서 삭제했어.

위 예시는 형식 참고용이야. 여기서 파이썬 코드를 작성할 때는 "파이썬 코딩 가이드"를 엄격히 준수해야 해.

### XML
```xml
<code_changes>
    <changed_files>
        <file>
            <file_summary>여기에 파일 변경 요약</file_summary>
            <file_operation>CREATE 또는 UPDATE 또는 DELETE</file_operation>
            <file_path>파일 경로</file_path>
            <file_code><![CDATA[
여기에 전체 코드 (CREATE나 UPDATE 경우)
]]></file_code>
        </file>
    </changed_files>
</code_changes>
```
