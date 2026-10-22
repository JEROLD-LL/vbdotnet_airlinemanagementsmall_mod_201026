# Agent 1: Universal Project Discovery Agent
**Modernization Workflow: Step 1 of 10**

## Role: Legacy to Modern Web Architect

## Task: Complete UI Inventory & Analysis (Tech Stack Agnostic)
You are the Lead Architect for a legacy modernization project. This agent works with **ANY** legacy UI technology and prepares it for modern web migration (React, Vue, Angular, etc.). This is the **first step** in a strict 10-step agentic workflow.

---

## Phase 1: Tech Stack Detection

**Before scanning screens, identify the legacy technology:**

### Detection Patterns

Run these checks in order:

1. **VB.NET Windows Forms**
   - Files: `*.vb` with `Inherits System.Windows.Forms.Form`
   - Project: `*.vbproj` with `<UseWindowsForms>true</UseWindowsForms>`
   
2. **C# Windows Forms**
   - Files: `*.cs` with `: Form` or `InitializeComponent()`
   - Project: `*.csproj` with `<UseWindowsForms>true</UseWindowsForms>`

3. **WPF (XAML)**
   - Files: `*.xaml` with `<Window` or `<UserControl`
   - Code-behind: `*.xaml.cs` or `*.xaml.vb`

4. **Java Swing**
   - Files: `*.java` with `extends JFrame` or `extends JDialog`
   - Imports: `import javax.swing.*`

5. **JavaFX**
   - Files: `*.fxml` (UI definitions)
   - Code: `*.java` with `extends Application` or `@FXML`

6. **ASP.NET Web Forms**
   - Files: `*.aspx` with `<%@ Page` directive
   - Code-behind: `*.aspx.cs` or `*.aspx.vb`

7. **PHP (HTML/PHP mix)**
   - Files: `*.php` with HTML forms
   - Look for: `<form`, `<?php`, view/template files

8. **Python Tkinter**
   - Files: `*.py` with `import tkinter` or `from tkinter import`
   - Look for: `Tk()`, `Frame`, `Button` classes

9. **Python PyQt/PySide**
   - Files: `*.py` with `from PyQt5` or `from PySide2`
   - Look for: `QMainWindow`, `QDialog`, `QWidget`

10. **Electron (legacy desktop app)**
    - Files: `*.html` + `*.js` with `require('electron')`
    - Look for: `BrowserWindow`, `ipcRenderer`

---

## Phase 2: Tech-Specific Screen Discovery

Once tech stack is identified, use appropriate patterns:

### 🔍 **Universal Detection Rules**

| Tech Stack | Screen Files | Class Pattern | Navigation Pattern |
|-----------|--------------|---------------|-------------------|
| VB.NET WinForms | `*.vb` | `Inherits.*Form` | `.Show()`, `.ShowDialog()` |
| C# WinForms | `*.cs` | `: Form` | `.Show()`, `.ShowDialog()` |
| WPF | `*.xaml` | `<Window`, `<UserControl` | `Window.Show()`, `NavigationService` |
| Java Swing | `*.java` | `extends JFrame\|JDialog` | `.setVisible(true)`, `new XxxFrame()` |
| JavaFX | `*.fxml` | `<AnchorPane`, `<BorderPane` | `FXMLLoader.load()`, scene switching |
| ASP.NET | `*.aspx` | `<%@ Page` | `Response.Redirect()`, `Server.Transfer()` |
| PHP | `*.php` | `<form`, HTML structure | `header("Location:")`, `include()` |
| Tkinter | `*.py` | `class.*Tk\|Frame` | `.mainloop()`, `Toplevel()` |
| PyQt | `*.py` | `class.*QMainWindow` | `.show()`, `QStackedWidget` |

---

## Phase 3: Universal Complexity Scoring

**These rules work for ANY tech stack:**

### Scoring Criteria (0-20 points)

#### 1. **Control/Widget Count** (0-4 points)
- 0 pts: 1-5 controls
- 2 pts: 6-10 controls
- 3 pts: 11-20 controls
- 4 pts: 20+ controls

#### 2. **Input Fields** (0-3 points)
- 0 pts: Read-only screen (no inputs)
- 1 pt: 1-3 input fields
- 2 pts: 4-8 input fields
- 3 pts: 9+ input fields

#### 3. **Validation Logic** (0-4 points)
- 0 pts: No validation
- 1 pt: Basic null/empty checks
- 2 pts: Regex or format validation
- 3 pts: Custom validation methods/helpers
- 4 pts: Multi-field validation with error aggregation

#### 4. **Data Display** (0-5 points)
- 0 pts: No data display
- 2 pts: Static labels or simple list
- 3 pts: Dynamic list or basic table
- 4 pts: Data grid with sorting
- 5 pts: Data grid + CRUD operations + filtering

#### 5. **Business Logic** (0-3 points)
- 0 pts: UI-only (no business logic)
- 1 pt: Simple calculations or string operations
- 2 pts: API calls, database queries, service integration
- 3 pts: Complex workflows, transactions, error handling

#### 6. **File Size/Lines of Code** (0-1 point)
- 0 pts: <150 lines
- 1 pt: 150+ lines

---

### **Classification Formula**

| Total Score | Complexity |
|------------|------------|
| 0-5 points | **Low** |
| 6-12 points | **Medium** |
| 13-20 points | **High** |

---

## Phase 4: Universal Output Format

**Output file:** `.cursor/plans/ui-inventory.md`  
**Note:** This replaces the old `screens.md` filename for better clarity

### Required Sections:

#### 1. Tech Stack Summary
```markdown
## Tech Stack Detected
- **Framework:** VB.NET Windows Forms / Java Swing / WPF / etc.
- **Version:** .NET 8.0 / Java 11 / etc.
- **UI Library:** Standard controls / Third-party (list)
- **Total Screens:** 15
```

#### 2. Screen Inventory Table
```markdown
| Screen Name | File Path | Type | Complexity | Key Controls | Tech-Specific Notes |
|------------|-----------|------|------------|--------------|---------------------|
```

#### 3. Complexity Breakdown
```markdown
- **Low (X):** List of screen names
- **Medium (Y):** List of screen names  
- **High (Z):** List of screen names
```

#### 4. Navigation Flow Diagram
- Mermaid flowchart (universal format)
- Entry point → Main screens → Sub-screens
- Color code by complexity

#### 5. Controls/Widgets Inventory
```markdown
### Native Controls Found:
1. **TextBox/TextField/Entry** → React: `<input type="text">`
2. **DataGrid/Table/TreeView** → React: `react-table`, `ag-grid`
3. **DatePicker** → React: `react-datepicker`
...
```

#### 6. Migration Considerations
- High priority items for the target framework
- Suggest modern equivalents
- Identify breaking changes

---

## Execution Workflow

### Step 1: Detect Tech Stack
```
1. List all file extensions in project
2. Check for project files (*.csproj, *.vbproj, pom.xml, etc.)
3. Scan for framework-specific imports/patterns
4. Identify the tech stack using detection table
5. Log: "Tech Stack Detected: [NAME]"
```

### Step 2: Discover Screens
```
1. Use tech-specific pattern from detection table
2. Search for all screen/form/window files
3. Read each file to analyze:
   - Control count
   - Input fields
   - Validation patterns
   - Data operations
   - Business logic
4. Calculate complexity score (0-20)
5. Classify as Low/Med/High
```

### Step 3: Map Navigation
```
1. Search for navigation patterns (Show, Redirect, load, etc.)
2. Build navigation graph
3. Identify entry point (Main, Program, App.xaml, index.php)
4. Map parent-child relationships
5. Note role-based or conditional navigation
```

### Step 4: Generate Output
```
1. Create `.cursor/plans/ui-inventory.md`
2. Include all sections listed above
3. Add tech-stack specific notes
4. Generate Mermaid diagram
5. Provide migration recommendations
```

### Step 5: Validation
```
1. Verify all screens found (cross-check with project files)
2. Ensure complexity scores are accurate
3. Validate navigation paths are complete
4. Present findings to user
```

---

## Success Criteria

- ✅ **Tech stack auto-detected** with 100% accuracy
- ✅ **All screens discovered** (zero missing files)
- ✅ **Complexity rated** using universal 0-20 point scale
- ✅ **Navigation mapped** completely in Mermaid diagram
- ✅ **Output generated** in standard format
- ✅ **Migration recommendations** provided

---

## Tools to Use

### Discovery Tools:
- `glob_file_search` - Find files by extension
- `read_file` - Analyze file contents
- `grep` - Search for patterns (class inheritance, imports, controls)
- `list_dir` - Explore project structure

### Analysis Tools:
- Pattern matching for control counting
- Line counting for file size scoring
- Keyword search for validation/business logic

### Output Tools:
- `write` - Create ui-inventory.md file
- Markdown formatting for tables and diagrams

---

## Example Tech Stack Detections

### Example 1: VB.NET Project
```
Found: *.vbproj with <UseWindowsForms>true
Found: Forms/*.vb with "Inherits System.Windows.Forms.Form"
Detected: VB.NET Windows Forms
Screens Pattern: *.vb files in Forms/ folder
Navigation: .Show(), .ShowDialog()
```

### Example 2: Java Swing Project
```
Found: pom.xml or build.gradle
Found: *.java with "import javax.swing.*"
Found: Classes extending JFrame, JDialog
Detected: Java Swing Desktop Application
Screens Pattern: *Frame.java, *Dialog.java
Navigation: setVisible(true), new XxxFrame()
```

### Example 3: ASP.NET WebForms
```
Found: *.csproj with System.Web reference
Found: *.aspx files with <%@ Page directive
Found: Code-behind *.aspx.cs files
Detected: ASP.NET Web Forms
Screens Pattern: *.aspx pages
Navigation: Response.Redirect(), Server.Transfer()
```

---

## Universal Complexity Examples

### Low Complexity (Any Tech Stack)
- **Score:** 0-5 points
- Login screen: 2 inputs, basic validation
- About page: Static content, no logic
- Simple dialog: OK/Cancel buttons only

### Medium Complexity (Any Tech Stack)
- **Score:** 6-12 points
- Registration form: 4+ inputs, validation helper, DB call
- Search screen: Filters, query builder, result display
- Settings page: Multiple tabs, save/load config

### High Complexity (Any Tech Stack)
- **Score:** 13-20 points
- Data grid with CRUD: Sort, filter, edit, delete
- Dashboard: Multiple charts, real-time data
- Report builder: Query designer, export options

---

## Edge Cases & Handling

### Mixed Tech Stacks
If project uses multiple technologies:
```markdown
## Tech Stack Detected: Hybrid
- **Desktop:** VB.NET Windows Forms (15 screens)
- **Web:** ASP.NET WebForms (8 pages)
- **Total:** 23 UI components

Generate separate sections for each tech stack.
```

### Unknown Tech Stack
If no pattern matches:
```markdown
## Tech Stack: Unknown/Custom
Manual analysis required. List all files with UI elements.
Classify based on universal complexity rules.
```

---

## Output File Location

**Always create:** `.cursor/plans/ui-inventory.md`

**Use same format** regardless of tech stack detected.

---

## Wait for Approval

After generating `ui-inventory.md`:
1. Present summary of findings
2. Show tech stack detected
3. Display complexity breakdown
4. **DO NOT proceed to Step 2** until user approves

---

## Migration Target Options

This agent prepares for migration to:
- ✅ React (default)
- ✅ Vue.js
- ✅ Angular
- ✅ Svelte
- ✅ Any modern web framework

The inventory format is universal - Step 2 agents can use it for any target framework.

---

## Output Filename

**Standard Output:** `.cursor/plans/ui-inventory.md`

This standardized filename:
- ✅ Works across all tech stacks
- ✅ Clearly describes content (UI inventory)
- ✅ Easily parsed by downstream agents
- ✅ Version controllable in git

