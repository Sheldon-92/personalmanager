# TAD Failure Patterns

## 🚨 Patterns That Lead to Project Problems

*Based on analysis of real TAD usage transcripts and quality gate failures*

### Failure Pattern 1: Agent Identity Confusion
**What happens:**
- Agent doesn't recognize their role as Agent A/B in TAD framework
- Responds as "Claude Code" instead of Alex/Blake
- Lacks awareness of TAD methodology and triangle collaboration

**Real Evidence:**
- Original menu-snap project: Agent B didn't know they were Blake
- Multiple correction attempts required from human
- Basic TAD framework concepts ignored

**Consequences:**
- Framework benefits completely lost
- No sub-agent utilization
- No quality gate execution
- Reverts to standard Claude behavior

**Prevention:**
- Mandatory startup checklist with identity verification
- Agent definition files with clear role statements
- Identity confirmation required before proceeding

### Failure Pattern 2: Creating Instead of Searching
**What happens:**
- Agent hears "professional version" and creates new solution
- Ignores keywords like "previous", "original", "our solution"
- Assumes innovation is better than adaptation

**Real Evidence:**
- Menu-snap project: Agent B created new preference interface instead of using existing "page 5" implementation
- User had to correct: "use our previous solution"
- Wasted time on unnecessary recreation

**Consequences:**
- Duplicate work and technical debt
- Inconsistent user experience
- Lost domain knowledge and business logic
- Longer development cycles

**Prevention:**
- Historical code search protocol in startup checklist
- Keyword trigger awareness training
- "Search first, create second" principle enforcement

### Failure Pattern 3: Function Assumption Errors
**What happens:**
- Agent assumes functions exist without verification
- Calls non-existent functions in implementation
- Code fails at runtime with function-not-found errors

**Real Evidence:**
- Menu-snap project line 182: Called `calculateScore(item, preferences)` - function doesn't exist
- Actual function was `calculateScoreAndReasons(item, preferences)`
- Caused 500 errors in production

**Consequences:**
- Application crashes and 500 errors
- User-facing functionality breaks
- Time wasted debugging obvious errors
- Quality gate failures

**Prevention:**
- Function existence verification in design gate
- Mandatory codebase search before implementation
- Bug-hunter sub-agent usage when in doubt

### Failure Pattern 4: Incomplete Data Flow Implementation
**What happens:**
- Backend calculates values (score, matchReasons, warnings)
- Frontend only displays basic fields (name, price)
- Critical user information becomes invisible

**Real Evidence:**
- Menu-snap project: Backend computed matchReasons and warnings
- Frontend showed only item name and price
- User safety information (allergies) was completely hidden

**Consequences:**
- User safety compromised (hidden allergy warnings)
- Poor user experience (no explanation for recommendations)
- Business logic benefits invisible to users
- Regulatory compliance failures

**Prevention:**
- Complete data flow mapping in design gate
- UI completeness verification in handoff template
- Safety-first design principle enforcement

### Failure Pattern 5: Visual Uniformity Disease
**What happens:**
- All items displayed with identical visual treatment
- No hierarchy or differentiation between recommendations
- Important information buried in uniform lists

**Real Evidence:**
- Menu-snap project: All items showed as "Good Options"
- No visual distinction between great vs. poor matches
- No prominence for safety warnings

**Consequences:**
- Users can't quickly identify best options
- Critical safety information not prominent
- Recommendation system value completely hidden
- Poor user decision-making support

**Prevention:**
- Visual hierarchy requirements in design specification
- Prominence requirements for safety information
- UX-expert-reviewer involvement in design

### Failure Pattern 6: No Sub-Agent Utilization
**What happens:**
- Agents work alone instead of using specialized sub-agents
- Complex tasks attempted without appropriate expertise
- Quality and efficiency suffer due to lack of specialization

**Real Evidence:**
- Menu-snap project: No sub-agent usage throughout entire implementation
- Bug-hunter could have prevented function call errors
- Test-runner could have caught data flow issues
- Parallel-coordinator could have handled multi-component work

**Consequences:**
- Lower quality output
- Longer development time
- Missed opportunities for specialized expertise
- Higher defect rates

**Prevention:**
- Sub-agent awareness verification in startup checklist
- Usage guidelines in agent definitions
- Task complexity assessment triggers

### Failure Pattern 7: Gate Skipping or Rushing
**What happens:**
- Quality gates are skipped to save time
- Checklists are marked complete without actual verification
- Issues are discovered later in process when more expensive to fix

**Real Evidence:**
- Menu-snap project: No evidence of systematic quality checking
- Function errors could have been caught in design gate
- Data flow issues could have been caught in implementation gate

**Consequences:**
- Expensive late-stage defect discovery
- User-facing quality issues
- Technical debt accumulation
- Repeated mistake patterns

**Prevention:**
- Mandatory gate execution protocols
- Evidence collection requirements
- Gate failure investigation procedures

### Failure Pattern 8: Domain Knowledge Ignorance
**What happens:**
- Agent lacks understanding of domain-specific concepts
- Cultural and safety considerations are missed
- Business context is not properly considered

**Real Evidence:**
- Menu-snap project: Agent didn't know "鱼香肉丝" (fish-fragrant pork) contains no fish
- Critical for allergy sufferers and cultural understanding
- Safety implications not recognized

**Consequences:**
- User safety risks (allergy misinformation)
- Cultural insensitivity and user confusion
- Business credibility damage
- Regulatory compliance failures

**Prevention:**
- Domain knowledge requirements in project setup
- Cultural consideration checklists
- Safety-first principle enforcement

## 🔄 Failure Pattern Prevention Strategy

### Early Detection
1. **Startup Checklist Verification**: Catch identity and awareness issues immediately
2. **Historical Search Requirements**: Prevent creation when adaptation possible
3. **Function Verification Gates**: Stop assumption-based errors before implementation

### Systematic Prevention
1. **Template Enforcement**: Use standardized handoff templates to ensure completeness
2. **Quality Gate Execution**: Systematic verification prevents late-stage issues
3. **Evidence Collection**: Track patterns to prevent repeated failures

### Cultural Change
1. **Safety-First Mindset**: User safety always takes priority
2. **Search-Before-Create**: Default to adaptation over innovation
3. **Evidence-Based Learning**: Use failure analysis to improve framework

## 📊 Failure Pattern Impact Analysis

### High-Impact Failures (User-Facing)
- Function assumption errors → Application crashes
- Incomplete data flow → Hidden safety information
- Visual uniformity → Poor user experience

### Medium-Impact Failures (Development)
- Creating instead of searching → Wasted development time
- No sub-agent utilization → Lower quality output
- Gate skipping → Late-stage rework

### Low-Impact Failures (Process)
- Agent identity confusion → Framework benefits lost
- Domain knowledge gaps → Suboptimal solutions

## 🎯 Failure Pattern Learning Application

### For Agent Training
- Use real failure examples as teaching tools
- Demonstrate consequence severity
- Practice prevention techniques
- Measure improvement through pattern reduction

### For Framework Evolution
- Update agent definitions based on failure analysis
- Enhance templates to prevent known failure modes
- Strengthen quality gates based on missed issues
- Create automated prevention where possible

### For Project Planning
- Review relevant failure patterns before starting
- Plan specific prevention measures
- Allocate time for proper verification
- Set up monitoring for early failure detection