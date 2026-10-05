from __future__ import annotations

import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, Preformatted, HRFlowable, Image,
)

ROOT = Path(__file__).resolve().parents[2]
HW5 = ROOT / "reports" / "hw05"
RAW = HW5 / "raw"
SHOTS = HW5 / "screenshots"
OUTPUT = HW5 / "Waingankar_HW5.pdf"
NAVY = colors.HexColor("#23578F")
BLUE = colors.HexColor("#4885C7")
PALE = colors.HexColor("#E7F0FA")
INK = colors.HexColor("#263548")
MUTED = colors.HexColor("#66788A")
CODE_BG = colors.HexColor("#F3F6F9")
CODE_BORDER = colors.HexColor("#C8D6E5")
WARN_BG = colors.HexColor("#FFF6DE")
WARN = colors.HexColor("#A46600")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=INK, alignment=TA_CENTER, spaceAfter=16))
styles.add(ParagraphStyle(name="H1HW", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=2, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name="H2HW", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=BLUE, spaceBefore=7, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="BodyHW", parent=styles["BodyText"], fontName="Helvetica", fontSize=11, leading=15, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallHW", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name="CaptionHW", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=7))
styles.add(ParagraphStyle(name="CellHW", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=INK))
styles.add(ParagraphStyle(name="HeadCellHW", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.white))
styles.add(ParagraphStyle(name="CodeHW", fontName="Courier", fontSize=7.2, leading=8.5, textColor=INK))
styles.add(ParagraphStyle(name="AlertHW", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=WARN, borderColor=colors.HexColor("#E5C77B"), borderWidth=0.7, borderPadding=7, backColor=WARN_BG, spaceBefore=4, spaceAfter=8))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def codebox(title, code):
    lines = []
    for line in code.strip("\n").expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line, width=112, subsequent_indent="    ", replace_whitespace=False, drop_whitespace=False) or [""])
    panel = Table([[Paragraph(f"<b>{escape(title)}</b>", styles["SmallHW"])], [Preformatted("\n".join(lines), styles["CodeHW"]) ]], colWidths=[7.15*inch], hAlign="LEFT")
    panel.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CODE_BG),("BOX",(0,0),(-1,-1),0.6,CODE_BORDER),("LINEBELOW",(0,0),(-1,0),0.5,CODE_BORDER),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    return panel


def source(rel, start, end=None, max_lines=30):
    lines=(ROOT/rel).read_text(encoding="utf-8").splitlines()
    a=next((i for i,line in enumerate(lines) if start in line),None)
    if a is None:
        return "# source excerpt unavailable: "+rel
    b=len(lines)
    if end:
        b=next((i for i in range(a+1,len(lines)) if end in lines[i]),len(lines))
    picked=lines[a:b]
    if len(picked)>max_lines:
        picked=picked[:max_lines]+["# ... excerpt shortened; consult the source file for full code"]
    return "\n".join(picked)


def p(text, style="BodyHW"):
    return Paragraph(text,styles[style])


def table(rows,widths,header=True):
    t=Table(rows,colWidths=widths,repeatRows=1 if header else 0,hAlign="LEFT")
    cmds=[("VALIGN",(0,0),(-1,-1),"TOP"),("GRID",(0,0),(-1,-1),0.35,CODE_BORDER),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]
    if header:
        cmds += [("BACKGROUND",(0,0),(-1,0),NAVY)]
        if len(rows)>1: cmds += [("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PALE])]
    t.setStyle(TableStyle(cmds))
    return t


def card(filename,description,width=3.52*inch):
    path=SHOTS/filename
    if path.exists():
        img=Image(str(path),width=width-10,height=1.12*inch,kind="proportional")
        content=[[img],[p(escape(filename),"CaptionHW")]]
        t=Table(content,colWidths=[width],hAlign="LEFT")
        t.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,CODE_BORDER),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
        return t
    content=p(f"<b>MANUAL SCREENSHOT REQUIRED</b><br/><b>{escape(filename)}</b><br/>{escape(description)}", "SmallHW")
    t=Table([[content]],colWidths=[width],rowHeights=[0.84*inch],hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),WARN_BG),("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#E5C77B")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t


def cards(items,cols=2):
    cells=[card(*item) for item in items]
    rows=[]
    for i in range(0,len(cells),cols):
        r=cells[i:i+cols]
        while len(r)<cols:r.append("")
        rows.append(r)
    t=Table(rows,colWidths=[3.57*inch]*cols,hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    return t


def heading(title,intro):
    return [p(title,"H1HW"),HRFlowable(width="100%",thickness=1,color=BLUE,spaceAfter=7),p(intro)]


class Report(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=letter,leftMargin=.62*inch,rightMargin=.62*inch,topMargin=.55*inch,bottomMargin=.58*inch,title="DATA 260 Homework 5 - Bhushan Waingankar",author="Bhushan Waingankar",subject="Restaurant inspection API, MCP tools, reliability, and Ollama agent")
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id="normal",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="main",frames=frame,onPage=self.footer)])
    @staticmethod
    def footer(canvas,doc):
        canvas.saveState()
        if doc.page>1:
            canvas.setStrokeColor(CODE_BORDER);canvas.line(.62*inch,.43*inch,7.88*inch,.43*inch)
            canvas.setFont("Helvetica",8);canvas.setFillColor(MUTED)
            canvas.drawString(.62*inch,.28*inch,"DATA 260 | HW5 DRAFT - screenshot evidence pending")
            canvas.drawRightString(7.88*inch,.28*inch,f"Page {doc.page}")
        canvas.restoreState()


meals=read_json(RAW/"mealdb_live_results.json")
mcp=read_json(RAW/"mcp_stdio_results.json")
scenarios=read_json(RAW/"agent_scenario_summary.json")
fault=read_json(HW5/"fault_injection_summary.json")
contracts=read_json(RAW/"domain_tool_contract_cases.json")
safety=read_json(RAW/"safety_examples.json")
maxsteps=read_json(RAW/"max_steps_example.json")
verification=read_json(HW5/"verification.json")
mealmap={x["tool"]:x for x in meals["results"]}

story=[]
# Cover page
story += [Spacer(1,.55*inch),p("DATA 260 - HOMEWORK 5","Cover"),p("Restaurant Inspection API, MCP Tools, Reliability, and Agent Loop","H2HW"),Spacer(1,.13*inch)]
repo='<link href="https://github.com/shoddy16/data260-7085" color="#23578F">https://github.com/shoddy16/data260-7085</link>'
story.append(p(f"<b>Student / Author:</b> Bhushan Waingankar<br/><b>Repository:</b> {repo}<br/><b>Domain:</b> Local restaurant inspections (DOMAIN_ID 5)"))
cfg=[[p("Value","HeadCellHW"),p("Configured value","HeadCellHW")],
 [p("SID4","CellHW"),p("7085","CellHW")],[p("PORT_BASE","CellHW"),p("8785","CellHW")],[p("PREFIX","CellHW"),p("s7085","CellHW")],[p("SEED","CellHW"),p("7085","CellHW")],[p("VERIFY_SEED","CellHW"),p("267085","CellHW")],[p("DOMAIN_ID","CellHW"),p("5 - Local restaurant inspections","CellHW")],[p("Hardware","CellHW"),p("Windows 10; Intel Core i5-6200U at 2.30 GHz; 4 logical CPUs; approximately 7.8 GB RAM","CellHW")],[p("Local model","CellHW"),p("Ollama llama3.2:3b at http://localhost:11434","CellHW")],[p("Tag / commit","CellHW"),p("Pending evidence capture and final Git commit. Base HEAD: fb6884388a43142bf983566125e4fc0070ddf557","CellHW")]]
story += [table(cfg,[1.8*inch,5.3*inch]),Spacer(1,.15*inch),p("DRAFT FOR EVIDENCE COMPLETION. Yellow panels identify required GUI screenshots not yet saved; they are placeholders, not evidence.","AlertHW"),p("The repository URL is included. Access for collaborators Sbnikitha and supriyaselvanganesan was not verified in this environment; confirm access before submission.","SmallHW"),PageBreak()]

# Part 1 DB
story += heading("1. Database and API","The HW4 FastAPI/MySQL service now includes a related Restaurant entity while retaining Inspection records. The additive migration preserved existing records, backfilled the relationship, and added constraints and timestamps.")
story += [p("Relationship and schema","H2HW"),codebox("Source excerpt - models/models.py", """class Restaurant(Base):
    __tablename__ = \"restaurants\"
    __table_args__ = (UniqueConstraint(\"code\", name=\"uq_restaurants_code\"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(500), nullable=False)
    code = Column(String(32), nullable=False, index=True)
    inspections = relationship(\"Inspection\", back_populates=\"restaurant\")

class Inspection(Base):
    restaurant_id = Column(Integer, ForeignKey(\"restaurants.id\", ondelete=\"RESTRICT\"), nullable=False)
    inspection_code = Column(String(64), nullable=False, unique=True)
    score = Column(Integer, nullable=False, default=100)
    restaurant = relationship(\"Restaurant\", back_populates=\"inspections\")"""),Spacer(1,6),p("The restrictive foreign key prevents deleting a restaurant while related inspections exist. The migration verification found 5,000 inspections linked to 5,001 restaurants, including the original Harbor Cafe row; no required fields were null and inspection codes were unique.")]
dbrows=[[p("Read-only check","HeadCellHW"),p("Observed result","HeadCellHW")],[p("Inspection data","CellHW"),p("5,000 rows; no null links or required HW5 values","CellHW")],[p("Restaurant data","CellHW"),p("5,001 rows, including the pre-existing Harbor Cafe","CellHW")],[p("Foreign key","CellHW"),p("inspections.restaurant_id -> restaurants.id; ON DELETE RESTRICT","CellHW")],[p("Paginated API","CellHW"),p("GET /restaurants/?skip=0&limit=1 and GET /inspections/?skip=0&limit=1 returned HTTP 200","CellHW")]]
story += [Spacer(1,5),table(dbrows,[1.65*inch,5.45*inch]),Spacer(1,8),cards([("P1-01-database-schema-and-rows.png","MySQL GUI showing tables, constraints, counts, and linked sample rows. Hide credentials.")]),PageBreak()]

# API actions
story += heading("1.1 API endpoints, CRUD, and validation","Both entities have create, paginated list, read-one, update, and delete endpoints. A relationship route returns inspections for a restaurant. Pydantic validation and CRUD handling return appropriate 404, 409, and 422 responses.")
story += [codebox("Source excerpt - routers/restaurants.py",source("routers/restaurants.py","@router.get(\"/\", response_model=list[RestaurantResponse])","@router.get(\"/{restaurant_id}\"",27)),Spacer(1,6),p("Automated API result: the post-change Python suite passed 24 tests. Actual test cases include HTTP 201 create, 200 reads/updates, 204 deletes, 404 missing resources, 409 duplicate/restrictive-delete conflicts, and 422 validation errors."),p("Postman screenshots - each action is a separate labeled capture. Use only newly created temporary evidence records and delete the child before its parent.","H2HW")]
api_slots=[("P1-02-restaurant-create.png","POST /restaurants/ - 201"),("P1-03-restaurant-list-pagination.png","GET /restaurants/?skip=0&limit=5"),("P1-04-restaurant-detail.png","GET /restaurants/{new_id}"),("P1-05-restaurant-update.png","PUT /restaurants/{new_id} - updated record"),("P1-06-restaurant-delete.png","DELETE the new parent after removing its child"),("P1-07-inspection-create.png","POST /inspections/ - linked child"),("P1-08-inspection-list-pagination.png","GET /inspections/?skip=0&limit=5"),("P1-09-inspection-detail.png","GET /inspections/{new_id}"),("P1-10-inspection-update.png","PUT /inspections/{new_id} - score update"),("P1-11-inspection-delete.png","DELETE the new inspection"),("P1-12-relationship.png","GET /restaurants/{new_id}/inspections"),("P1-13-404.png","GET /restaurants/99999 - 404"),("P1-14-409.png","Delete parent while child exists - 409"),("P1-15-validation.png","POST with malformed restaurant code - 422")]
story += [cards(api_slots),PageBreak()]

# Redux
story += heading("1.2 Redux Toolkit client","Axios and Redux Toolkit async thunks connect React screens to FastAPI. Slice reducers update state after successful create, update, and delete operations; errors are returned to the UI.")
story += [codebox("Source excerpt - frontend/src/features/inspections/inspectionsSlice.js", """export const fetchInspections = createAsyncThunk(
  \"inspections/fetchAll\",
  async (_, { rejectWithValue }) => {
    try { return (await api.get(\"/inspections/\")).data; }
    catch (error) { return rejectWithValue(errorMessage(error, \"Could not load inspections.\")); }
  },
);

.addCase(createInspection.fulfilled, (state, action) => { state.items.unshift(action.payload); })
.addCase(updateInspection.fulfilled, (state, action) => {
  const index = state.items.findIndex((item) => item.id === action.payload.id);
  if (index !== -1) state.items[index] = action.payload;
})
.addCase(deleteInspection.fulfilled, (state, action) => {
  state.items = state.items.filter((item) => item.id !== action.payload);
});"""),Spacer(1,7),p("The frontend production build passed with 96 modules transformed. The assignment requires each UI screenshot to pair the relevant Redux code and corresponding browser result in one frame."),cards([("P1-16-redux-home.png","Home/list UI plus list thunk or slice"),("P1-17-redux-create.png","Create form/result plus create thunk or slice"),("P1-18-redux-update.png","Update flow/result plus update thunk or slice"),("P1-19-redux-delete.png","Delete flow/list result plus delete thunk or slice")]),PageBreak()]

# Meals
story += heading("2. MCP servers - TheMealDB","The local `meals` MCP server exposes four tools. Real calls to the public TheMealDB service completed; actual JSON is preserved in raw/mealdb_live_results.json.")
story += [codebox("Source excerpt - meals_server.py", """@mcp.tool()
async def search_meals_by_name(query: str, limit: int = 5) -> dict:
    return await mealdb.search_meals_by_name(query, limit)

@mcp.tool()
async def meals_by_ingredient(ingredient: str, limit: int = 12) -> dict:
    return await mealdb.meals_by_ingredient(ingredient, limit)

@mcp.tool()
async def random_meal() -> dict:
    return await mealdb.random_meal()

@mcp.tool()
async def meal_details(id: str | int) -> dict:
    return await mealdb.meal_details(id)"""),Spacer(1,6)]
mealrows=[[p("Tool","HeadCellHW"),p("Actual live result","HeadCellHW"),p("Returned fields","HeadCellHW")]]
for name in ["search_meals_by_name","meals_by_ingredient","random_meal","meal_details"]:
    item=next(x for x in meals["results"] if x["tool"]==name); result=item["result"]
    if name=="search_meals_by_name":
        row=(result.get("meals") or [{}])[0]; desc=f"{row.get('name')} (id {row.get('id')})"; fields="id, name, area, category, thumb"
    elif name=="meals_by_ingredient":
        desc=", ".join(x.get("name","") for x in result.get("meals",[]));fields="id, name, thumb"
    elif name=="random_meal":
        desc=f"{result.get('name')} (id {result.get('id')})";fields="full recipe, instructions, image, source, video, ingredients"
    else:
        desc=f"{result.get('name')} (id {result.get('id')})";fields="full recipe, instructions, image, source, video, ingredients"
    mealrows.append([p(name,"CellHW"),p(escape(desc),"CellHW"),p(escape(fields),"CellHW")])
story += [table(mealrows,[1.9*inch,2.25*inch,2.95*inch]),Spacer(1,7),p("Inspector screenshots - show the selected tool, exact input, and real returned output.","H2HW"),cards([("P2-01-meal-search.png","Search name Arrabiata; limit 2"),("P2-02-meal-ingredient.png","Ingredient chicken; limit 2"),("P2-03-meal-random.png","Random meal; no input"),("P2-04-meal-details.png","Meal id 52772")]),PageBreak()]

# Domain MCP
story += heading("2.1 MCP server - restaurant domain","The domain server declares exactly `search`, `detail_lookup`, and `aggregate`. All tools use the same `{ok, data, error}` envelope. MCP Inspector was used for valid and deliberately invalid calls; JSON receipts are preserved under raw/.")
story += [codebox("Source excerpt - domain_mcp_server.py", """@mcp.tool()
def search(query: str, limit: int = 5) -> dict:
    return default_inspection_tools.search(query, limit)

@mcp.tool()
def detail_lookup(inspection_id: int) -> dict:
    return default_inspection_tools.detail_lookup(inspection_id)

@mcp.tool()
def aggregate(group_by: str = \"category\") -> dict:
    return default_inspection_tools.aggregate(group_by)"""),Spacer(1,6)]
contractrows=[[p("Tool / expected input","HeadCellHW"),p("Rejected input","HeadCellHW"),p("Returned error envelope","HeadCellHW"),p("Reason","HeadCellHW")]]
for x in contracts:
    contractrows.append([p(escape(x["tool"]+": "+str(x["expected_input_schema"])),"CellHW"),p(escape(json.dumps(x["invalid_input"])),"CellHW"),p(escape(json.dumps(x["invalid_output"])),"CellHW"),p(escape(x["rejection_reason"]),"CellHW")])
story += [table(contractrows,[1.65*inch,1.05*inch,2.8*inch,1.6*inch]),Spacer(1,5),p("Live category aggregation returned 1,686 Food Safety, 1,683 Health and Safety, and 1,631 Sanitation records. A detail call returned inspection id 4 for Restaurant 1. The rejected-call JSON preserves the error outputs and explains why each input is invalid.","SmallHW"),p("Inspector screenshots - one success and one invalid call for each domain tool.","H2HW"),cards([("P2-05-domain-search-ok.png","search: Restaurant 1, limit 2"),("P2-06-domain-search-invalid.png","search: blank query"),("P2-07-domain-detail-ok.png","detail_lookup: id 4"),("P2-08-domain-detail-invalid.png","detail_lookup: id 0"),("P2-09-domain-aggregate-ok.png","aggregate: group_by category"),("P2-10-domain-aggregate-invalid.png","aggregate: group_by email")]),PageBreak()]

# Reliability
story += heading("3. Tool contracts under stress","External API and read operations use timeouts and bounded exponential backoff. A seeded fault injector ran 50 calls at each required failure rate; the full 150-record CSV/JSONL dataset is preserved.")
story += [codebox("Source excerpt - reliability.py", """def _backoff_seconds(failed_attempt, base, maximum):
    return min(base * (2**failed_attempt), maximum)

for attempt in range(max_attempts):
    try:
        return operation()
    except Exception as error:
        if attempt + 1 >= max_attempts or not retryable(error):
            raise
        sleep(_backoff_seconds(attempt, base_backoff_seconds, max_backoff_seconds))"""),Spacer(1,6)]
frows=[[p("Injected failure","HeadCellHW"),p("Calls","HeadCellHW"),p("Success","HeadCellHW"),p("Mean latency","HeadCellHW"),p("p99 latency","HeadCellHW")]]
for m in fault["metrics"]:
    frows.append([p(f"{m['failure_rate']:.0%}","CellHW"),p(str(m["calls"]),"CellHW"),p(f"{m['success_rate_percent']:.1f}%","CellHW"),p(f"{m['mean_latency_ms']:.4f} ms","CellHW"),p(f"{m['p99_latency_ms']:.4f} ms","CellHW")])
story += [table(frows,[1.3*inch,.75*inch,1.2*inch,1.85*inch,1.8*inch]),Spacer(1,6),p("Policy: three attempts; 50 ms base backoff; 200 ms cap; 1 ms simulated operation work. At 50% injected failure, five of fifty calls failed. This bounded policy is useful for occasional interactive failures; batch jobs can use a larger retry budget and longer delay cap while retaining per-item failures.")]
demorows=[[p("Demonstration","HeadCellHW"),p("Attempts","HeadCellHW"),p("Actual outcome","HeadCellHW")],[p("First-attempt success","CellHW"),p("1","CellHW"),p("ok","CellHW")],[p("Retry then success","CellHW"),p("2","CellHW"),p("ok","CellHW")],[p("Retry exhaustion","CellHW"),p("3","CellHW"),p("all attempts failed","CellHW")]]
story += [table(demorows,[2.3*inch,1.2*inch,3.4*inch]),Spacer(1,7),cards([("P3-01-fault-injection-run.png","Terminal: 150 calls, 50 at each rate"),("P3-02-retry-examples.png","Actual first success, retry success, exhaustion"),("P3-03-metrics.png","Measured success, mean, and p99")]),PageBreak()]

# Safe tool and offline
story += heading("4. One safe tool entry point and offline tests","`execute_tool()` is the single domain-tool dispatcher for the agent. It validates inputs, applies the restaurant-inspection safety rule, catches errors, and serializes the common result envelope.")
story += [codebox("Source excerpt - tool_executor.py", """if _is_safety_blocked(name, inputs):
    return json.dumps(failure(\"safety rule blocked requests to evade or falsify restaurant inspections\"))

handlers = {
    \"search\": lambda: domain_tools.search(inputs.get(\"query\"), inputs.get(\"limit\", 5)),
    \"detail_lookup\": lambda: domain_tools.detail_lookup(inputs.get(\"inspection_id\")),
    \"aggregate\": lambda: domain_tools.aggregate(inputs.get(\"group_by\", \"category\")),
}
try:
    envelope = handler()
except Exception:
    envelope = failure(\"tool execution failed\")
return json.dumps(envelope, ensure_ascii=False, separators=(\",\", \":\"))"""),Spacer(1,6),p("Actual fixture examples","H2HW"),codebox("raw/safety_examples.json",json.dumps(safety,indent=2)),Spacer(1,6),p("The allowed Harbor search returned one fixture record with `ok: true`. The prohibited request returned `ok: false`, `data: null`, and a clear safety error without raising an exception."),PageBreak()]
story += heading("4.1 Offline test results","The post-change Python suite passed 24 tests. The offline assert runner passed all nine checks without a live database, Internet API, or model.")
story += [codebox("Actual console output - run_offline_tests.py", """PASS: search valid
PASS: search invalid blank query
PASS: detail valid
PASS: detail invalid id
PASS: aggregate valid
PASS: aggregate invalid group
PASS: safety rule blocks evasion
PASS: MockModel stops at max_steps
PASS: MealDB shape and limit (mocked)
OFFLINE ASSERTIONS: 9/9 passed"""),Spacer(1,6),codebox("Actual MockModel result - raw/max_steps_example.json",json.dumps(maxsteps,indent=2)),Spacer(1,7),cards([("P4-01-offline-tests.png","Terminal with every PASS and final 9/9"),("P4-02-safety-allowed.png","Allowed fixture envelope"),("P4-03-safety-blocked.png","Blocked safety envelope"),("P4-04-max-steps.png","MockModel reaching max_steps")]),PageBreak()]

# Agent
story += heading("5. Agent loop, safety, and metrics","`run_agent()` asks the local model for a structured action, routes tool calls through `execute_tool()`, inspects results, records each step, and stops at `max_steps`. The required model remained llama3.2:3b.")
story += [codebox("Source excerpt - agent.py", """while step_count < max_steps:
    step_count += 1
    action = agent_model.next_action(messages)
    # Validate the structured action and dispatch through execute_tool.
    result_text = tool_executor(tool_name, tool_inputs)
    result = json.loads(result_text)
    # Add the actual result to the next model turn and append a JSONL step.
    if step_count >= max_steps:
        stop_reason = \"max_steps\"
        break"""),Spacer(1,6)]
srows=[[p("Scenario","HeadCellHW"),p("Tool","HeadCellHW"),p("Steps","HeadCellHW"),p("Tool calls","HeadCellHW"),p("Stop reason","HeadCellHW")]]
for s in scenarios:
    srows.append([p(escape(s["prompt"]),"CellHW"),p(", ".join(s.get("tools",[])),"CellHW"),p(str(s["step_count"]),"CellHW"),p(str(s["tool_call_count"]),"CellHW"),p(escape(s["stop_reason"]),"CellHW")])
story += [table(srows,[2.55*inch,1.15*inch,.62*inch,.82*inch,1.45*inch]),Spacer(1,6),p("All four focused real Ollama scenarios completed normally in two model steps with one tool call. Their run IDs, answers, and tool names are in raw/agent_scenario_summary.json; full step events are in raw/agent_runs.jsonl. An oversized per-restaurant aggregate timed out and remains recorded separately; it is not described as a success.","SmallHW"),cards([("P5-01-agent-scenarios.png","Terminal with four prompts, steps, stop reasons, and tool counts"),("P5-02-agent-log.png","Actual JSONL step and run completion records")]),PageBreak()]

# Reflection / AI use
story += heading("5.1 Reflection","The following reflection is based on the actual successful Ollama search run recorded in raw/agent_runs.jsonl.")
reflection=(HW5/"REFLECTION.md").read_text(encoding="utf-8")
for para in [x.strip() for x in reflection.split("\n\n") if x.strip() and not x.startswith("#")]: story.append(p(escape(para)))
story += [p("The reflection is 200-300 words as required.","CaptionHW"),PageBreak()]
story += heading("6. AI Use","AI-use disclosure included in the report as required by the assignment.")
for line in (HW5/"AI_USE.md").read_text(encoding="utf-8").splitlines():
    if line.startswith("#") or not line.strip(): continue
    story.append(p(escape(line)))
story += [PageBreak()]

# Verification / close
story += heading("7. Verification and remaining evidence",f"The consolidated script passed {len(verification['checks'])} checks on the working tree, including the Python suite, offline assertions, Vite build, read-only MySQL/API checks, saved MCP and MealDB results, four normal real Ollama runs, and the 150-record experiment dataset.")
vrows=[[p("Verification check","HeadCellHW"),p("Result","HeadCellHW")]]
for check in verification["checks"]: vrows.append([p(escape(check["name"]),"CellHW"),p("PASS" if check["passed"] else "FAIL","CellHW")])
story += [table(vrows,[5.9*inch,.95*inch]),Spacer(1,8),p("This remains a draft. Zero GUI screenshots have been saved; collaborator access has not been confirmed; the final submission PDF, commit, and `hw5` tag are still pending. After saving the named screenshots under reports/hw05/screenshots/, rerun this builder to replace each yellow placeholder with the actual image, visually inspect the updated PDF, refresh verification, then commit and tag the finished state.","AlertHW")]

doc=Report(OUTPUT)
doc.build(story)
print(f"Created {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
