You are helping to plan and document the mission, roadmap and tech stack for modernizing a legacy codebase to a target tech-stack.  This will include:

- **Gathering Information**: The user's product vision, user personas, problems and key features
- **Mission Document**: Take what you've gathered and create a concise mission document
- **Roadmap**: Create a phased development plan with prioritized features
- **Tech stack**: Establish the target technical stack for modernizing the legacy codebase

The goal is to use the provided legacy code, FSD (Functional Specification Document), and MCM (Meta Cognitive Model) to plan the modernization of the current legacy code to the target tech-stack.

Carefully read and execute the instructions in the following files IN SEQUENCE, following their numbered file names.  Only proceed to the next numbered instruction file once the previous numbered instruction has been executed.

Instructions to follow in sequence:

# REQUIRED INPUTS CHECK

Before proceeding with any phase, verify that the following 4 required inputs have been provided:

1. **Path to Legacy Code**: The directory path containing the legacy codebase to be modernized
2. **Path to FSD.md**: The path to the Functional Specification Document (FSD.md)
3. **Path to mcm.json**: The path to the Meta Cognitive Model file (mcm.json)
4. **Path to target-tech-stack.json**: The path to the Target Tech Stack JSON file defining the modernization target

If any of these paths are NOT provided, prompt the user:
```
To proceed with legacy code modernization planning, please provide the following required inputs:

1. Path to Legacy Code: [directory path to your legacy codebase]
2. Path to FSD.md: [path to your Functional Specification Document]
3. Path to mcm.json: [path to your Meta Cognitive Model file]
4. Path to target-tech-stack.json: [path to your Target Tech Stack JSON file]

These files will be used to analyze your legacy code and plan its modernization to the target tech-stack.
```

Once all 4 paths are provided, READ and analyze each file to understand:
- The current legacy code structure and patterns (from legacy code path)
- The functional requirements and specifications (from FSD.md)
- The code component model and relationships (from mcm.json)
- The target technology stack for modernization (from target-tech-stack.json)

Then proceed to PHASE 1.

# PHASE 1: Product Concept

This begins a multi-step process for planning and documenting the mission and roadmap for modernizing the legacy codebase.

The FIRST STEP is to confirm the product details by following these instructions:

Collect comprehensive product information from the user:

```bash
# Check if product folder already exists
if [ -d "leap-os/product" ]; then
    echo "Product documentation already exists. Review existing files or start fresh?"
    # List existing product files
    ls -la leap-os/product/
fi
```

Gather from user the following required information (use the FSD.md, mcm.json, and target-tech-stack.json to extract this where possible):
- **Product Idea**: Core concept and purpose (required) - derive from FSD.md if available
- **Key Features**: Minimum 3 features with descriptions - extract from FSD.md and legacy code analysis
- **Target Users**: At least 1 user segment with use cases - derive from FSD.md if available
- **Target Tech stack**: Confirmation of the target tech stack for modernization - extract from target-tech-stack.json

If any required information is missing, prompt user:
```
Please provide the following to create your modernization plan:
1. Main idea for the product (or confirm from FSD.md)
2. List of key features (minimum 3) - will extract from FSD.md and legacy code
3. Target users and use cases (minimum 1)
4. Confirm the target tech stack for modernization (or update target-tech-stack.json)
```


Then WAIT for me to give you specific instructions on how to use the information you've gathered to create the mission and roadmap.


## User Standards & Preferences Compliance

When planning the product's tech stack, mission statement and roadmap, use the user's standards and preferences for context and baseline assumptions, as documented in these files:

@leap-os/standards/global/coding-style.md
@leap-os/standards/global/commenting.md
@leap-os/standards/global/conventions.md
@leap-os/standards/global/error-handling.md
@leap-os/standards/global/tech-stack.md
@leap-os/standards/global/validation.md

# PHASE 2: Create Mission

Now that you've gathered information about this product, use that info to create the mission document in `leap-os/product/mission.md` by following these instructions:

Create `leap-os/product/mission.md` with comprehensive product definition following this structure for its' content:

#### Mission Structure:
```markdown
# Product Mission

## Pitch
[PRODUCT_NAME] is a [PRODUCT_TYPE] that helps [TARGET_USERS] [SOLVE_PROBLEM]
by providing [KEY_VALUE_PROPOSITION].

## Users

### Primary Customers
- [CUSTOMER_SEGMENT_1]: [DESCRIPTION]
- [CUSTOMER_SEGMENT_2]: [DESCRIPTION]

### User Personas
**[USER_TYPE]** ([AGE_RANGE])
- **Role:** [JOB_TITLE/CONTEXT]
- **Context:** [BUSINESS/PERSONAL_CONTEXT]
- **Pain Points:** [SPECIFIC_PROBLEMS]
- **Goals:** [DESIRED_OUTCOMES]

## The Problem

### [PROBLEM_TITLE]
[PROBLEM_DESCRIPTION]. [QUANTIFIABLE_IMPACT].

**Our Solution:** [SOLUTION_APPROACH]

## Differentiators

### [DIFFERENTIATOR_TITLE]
Unlike [COMPETITOR/ALTERNATIVE], we provide [SPECIFIC_ADVANTAGE].
This results in [MEASURABLE_BENEFIT].

## Key Features

### Core Features
- **[FEATURE_NAME]:** [USER_BENEFIT_DESCRIPTION]

### Collaboration Features
- **[FEATURE_NAME]:** [USER_BENEFIT_DESCRIPTION]

### Advanced Features
- **[FEATURE_NAME]:** [USER_BENEFIT_DESCRIPTION]
```

#### Important Constraints

- **Focus on user benefits** in feature descriptions, not technical details
- **Keep it concise** and easy for users to scan and get the more important concepts quickly



## User Standards & Preferences Compliance

IMPORTANT: Ensure the product mission is ALIGNED and DOES NOT CONFLICT with the user's preferences and standards as detailed in the following files:

@leap-os/standards/global/coding-style.md
@leap-os/standards/global/commenting.md
@leap-os/standards/global/conventions.md
@leap-os/standards/global/error-handling.md
@leap-os/standards/global/tech-stack.md
@leap-os/standards/global/validation.md

# PHASE 3: Create Roadmap

Now that you've created this product's mission.md, use that to guide your creation of the roadmap in `leap-os/product/roadmap.md` by following these instructions:

Generate `leap-os/product/roadmap.md` with an ordered feature checklist:

Do not include any tasks for initializing a new codebase or bootstrapping a new application. Assume the user is already inside the project's codebase and has a bare-bones application initialized.

#### Creating the Roadmap:

1. **Review the Mission** - Read `leap-os/product/mission.md` to understand the product's goals, target users, and success criteria.

2. **Identify Features** - Based on the mission, determine the list of concrete features needed to achieve the product vision.

3. **Strategic Ordering** - Order features based on:
   - Technical dependencies (foundational features first)
   - Most direct path to achieving the mission
   - Building incrementally from MVP to full product

4. **Create the Roadmap** - Use the structure below as your template. Replace all bracketed placeholders (e.g., `[FEATURE_NAME]`, `[DESCRIPTION]`, `[EFFORT]`) with real content that you create based on the mission.

#### Roadmap Structure:
```markdown
# Product Roadmap

1. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
2. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
3. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
4. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
5. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
6. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
7. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`
8. [ ] [FEATURE_NAME] — [1-2 SENTENCE DESCRIPTION OF COMPLETE, TESTABLE FEATURE] `[EFFORT]`

> Notes
> - Order items by technical dependencies and product architecture
> - Each item should represent an end-to-end (frontend + backend) functional and testable feature
```

Effort scale:
- `XS`: 1 day
- `S`: 2-3 days
- `M`: 1 week
- `L`: 2 weeks
- `XL`: 3+ weeks

#### Important Constraints

- **Make roadmap actionable** - include effort estimates and dependencies
- **Priorities guided by mission** - When deciding on order, aim for the most direct path to achieving the mission as documented in mission.md
- **Ensure phases are achievable** - start with MVP, build incrementally



## User Standards & Preferences Compliance

IMPORTANT: Ensure the product roadmap is ALIGNED and DOES NOT CONFLICT with the user's preferences and standards as detailed in the following files:

@leap-os/standards/global/coding-style.md
@leap-os/standards/global/commenting.md
@leap-os/standards/global/conventions.md
@leap-os/standards/global/error-handling.md
@leap-os/standards/global/tech-stack.md
@leap-os/standards/global/validation.md

# PHASE 4: Create Tech Stack

The final part of our product planning process is to document this product's tech stack in `leap-os/product/tech-stack.md`.  Follow these instructions to do so:

Create `leap-os/product/tech-stack.md` with a list of all tech stack choices that cover all aspects of this product's codebase.

### Creating the Tech Stack document

#### Step 1: Read the Target Tech Stack JSON

READ and analyze the `target-tech-stack.json` file provided as a required input. This file contains the primary target tech stack for modernization and should serve as the foundation for the tech stack document.

#### Step 2: Note User's Input Regarding Tech Stack

IF the user has provided specific information in the current conversation in regards to tech stack choices, these notes ALWAYS take precedence over other sources. These must be reflected in your final `tech-stack.md` document that you will create.

#### Step 3: Gather User's Default Tech Stack Information

Reconcile and fill in the remaining gaps in the tech stack list by finding, reading and analyzing information regarding the tech stack. Find this information in the following sources, in this order:

1. If user has provided their default tech stack under "User Standards & Preferences Compliance", READ and analyze this document.
2. If the current project has any of these files, read them to find information regarding tech stack choices for this codebase:
  - `claude.md`
  - `agents.md`

#### Step 4: Create the Tech Stack Document

Create `leap-os/product/tech-stack.md` and populate it with the final list of all technical stack choices, reconciled between the target-tech-stack.json, information the user has provided to you, and the information found in other sources.


## Display confirmation and next step

Once you've created tech-stack.md, output the following message:

```
✅ I have documented the product's tech stack at `leap-os/product/tech-stack.md`.

Review it to ensure all of the tech stack details are correct for this product.

You're ready to start planning a feature spec! You can do so by running `shape-spec.md` or `write-spec.md`.
```

## User Standards & Preferences Compliance

The target-tech-stack.json file provided as a required input serves as the primary source for tech stack decisions. The user may also provide additional information regarding their tech stack in conversation, which should take precedence when documenting the product's tech stack. To fill in any gaps, find the user's usual tech stack information as documented in any of these files:

@leap-os/standards/global/coding-style.md
@leap-os/standards/global/commenting.md
@leap-os/standards/global/conventions.md
@leap-os/standards/global/error-handling.md
@leap-os/standards/global/tech-stack.md
@leap-os/standards/global/validation.md
