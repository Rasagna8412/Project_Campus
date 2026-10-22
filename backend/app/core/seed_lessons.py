"""Structured Seed Content for Milestone 3 Lessons and Sections.

Provides verified, curriculum-aligned academic lessons in Physics, Chemistry,
and Mathematics with LaTeX equations, step-by-step examples, learning objectives,
and distinct draft/in-review entries for publication exclusion verification.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentStatus, Lesson, LessonSection, SectionType
from app.models.taxonomy import BoardCurriculum, Chapter, GradeStage, Subject, Topic

logger = logging.getLogger(__name__)

SAMPLE_LESSONS_DATA = [
    {
        "board_code": "CBSE",
        "grade_code": "CLASS_12",
        "subject_code": "PHYSICS",
        "chapter_number": 1,
        "chapter_title": "Electric Charges and Fields",
        "chapter_slug": "electric-charges-and-fields",
        "chapter_summary": "Study of stationary electric charges, electrostatic forces, electric fields, dipoles, and Gauss's law.",
        "topics": [
            {
                "topic_number": 1,
                "title": "Coulomb's Law and Principle of Superposition",
                "slug": "coulombs-law-and-superposition",
                "importance_weight": 3,
                "lessons": [
                    {
                        "title": "Coulomb's Law, Electrostatic Force, and the Superposition Principle",
                        "slug": "coulombs-law-and-superposition-principle",
                        "summary": "Comprehensive analysis of Coulomb's inverse-square law, vector formulation, permittivity of free space, relative permittivity, and vector superposition of forces.",
                        "learning_objectives": [
                            "State Coulomb's Law in scalar and vector formulations",
                            "Understand the role of permittivity and dielectric constant",
                            "Calculate the net electrostatic force on a point charge due to multiple surrounding charges using vector superposition",
                            "Differentiate between electrostatic force and gravitational force between subatomic particles",
                        ],
                        "estimated_read_time_minutes": 12,
                        "status": ContentStatus.PUBLISHED.value,
                        "provenance": "Aligned with CBSE Class 12 Physics (NCERT Chapter 1, Section 1.4 & 1.5). Verified by Senior Physics Faculty.",
                        "is_verified": True,
                        "display_order": 1,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "Introduction and Statement of Coulomb's Law",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "In 1785, French physicist Charles-Augustin de Coulomb quantified the electrostatic force of attraction or repulsion between two stationary, charged point particles using a sensitive torsion balance.\n\n"
                                    "### The Scalar Form\n"
                                    "The magnitude of the electrostatic force $F$ between two stationary point charges $q_1$ and $q_2$ separated by a distance $r$ in a vacuum is directly proportional to the product of the magnitudes of the charges and inversely proportional to the square of the distance between them:\n\n"
                                    "$$F = k \\frac{|q_1 q_2|}{r^2}$$\n\n"
                                    "Where $k$ is the electrostatic constant of proportionality in SI units:\n\n"
                                    "$$k = \\frac{1}{4\\pi\\varepsilon_0} \\approx 8.98755 \\times 10^9 \\text{ N}\\cdot\\text{m}^2/\\text{C}^2$$\n\n"
                                    "Here, $\\varepsilon_0$ denotes the **permittivity of free space** (vacuum):\n\n"
                                    "$$\\varepsilon_0 = 8.854187 \\times 10^{-12} \\text{ C}^2/(\\text{N}\\cdot\\text{m}^2)$$"
                                ),
                            },
                            {
                                "section_number": 2,
                                "title": "Vector Formulation of Coulomb's Law",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "Electrostatic forces are directed along the line joining the centers of the two point charges, adhering to Newton's Third Law (${\\vec{F}}_{12} = -{\\vec{F}}_{21}$).\n\n"
                                    "Let $\\vec{r}_1$ and $\\vec{r}_2$ be the position vectors of charges $q_1$ and $q_2$. The displacement vector from $q_1$ to $q_2$ is $\\vec{r}_{21} = \\vec{r}_2 - \\vec{r}_1$, with unit vector $\\hat{r}_{21} = \\frac{\\vec{r}_{21}}{|\\vec{r}_{21}|}$.\n\n"
                                    "The force ${\\vec{F}}_{21}$ exerted on charge $q_2$ by charge $q_1$ is:\n\n"
                                    "$${\\vec{F}}_{21} = \\frac{1}{4\\pi\\varepsilon_0} \\frac{q_1 q_2}{|\\vec{r}_2 - \\vec{r}_1|^2} \\hat{r}_{21}$$\n\n"
                                    "* When $q_1 q_2 > 0$ (like charges): ${\\vec{F}}_{21}$ is along $\\hat{r}_{21}$ (repulsive force).\n"
                                    "* When $q_1 q_2 < 0$ (unlike charges): ${\\vec{F}}_{21}$ is opposite to $\\hat{r}_{21}$ (attractive force)."
                                ),
                            },
                            {
                                "section_number": 3,
                                "title": "Effect of Dielectric Medium",
                                "section_type": SectionType.KEY_FORMULA.value,
                                "content_markdown": (
                                    "When point charges are immersed in an insulating material (dielectric medium) with relative permittivity (dielectric constant) $\\varepsilon_r = K$, the net electrostatic force is reduced:\n\n"
                                    "$$F_{\\text{medium}} = \\frac{1}{4\\pi\\varepsilon} \\frac{|q_1 q_2|}{r^2} = \\frac{F_{\\text{vacuum}}}{K}$$\n\n"
                                    "For vacuum, $K = 1$; for dry air at STP, $K \\approx 1.00059$; for pure water at $20^\\circ\\text{C}$, $K \\approx 80.4$."
                                ),
                            },
                            {
                                "section_number": 4,
                                "title": "The Principle of Superposition",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "Experimental observations confirm that the interaction between any two charges is completely independent of the presence of all other charges.\n\n"
                                    "The net electrostatic force exerted on a test charge $q_0$ due to a collection of $n$ stationary discrete point charges $q_1, q_2, \\dots, q_n$ is the vector sum of the individual forces:\n\n"
                                    "$${\\vec{F}}_{\\text{net}} = {\\vec{F}}_{01} + {\\vec{F}}_{02} + \\dots + {\\vec{F}}_{0n} = \\sum_{i=1}^{n} \\frac{1}{4\\pi\\varepsilon_0} \\frac{q_0 q_i}{|\\vec{r}_0 - \\vec{r}_i|^2} \\hat{r}_{0i}$$"
                                ),
                            },
                            {
                                "section_number": 5,
                                "title": "Worked Example: Triangular Charge Configuration",
                                "section_type": SectionType.WORKED_EXAMPLE.value,
                                "content_markdown": (
                                    "**Problem Statement:** Three equal positive point charges $q = +2.0\\,\\mu\\text{C}$ are placed at the vertices of an equilateral triangle with side length $a = 0.50\\text{ m}$. Calculate the magnitude of the net electrostatic force on each charge.\n\n"
                                    "**Step 1: Identify symmetry and individual forces**\n"
                                    "By symmetry, each charge experiences two forces of identical magnitude $F_0$ from the other two charges:\n\n"
                                    "$$F_0 = \\frac{1}{4\\pi\\varepsilon_0} \\frac{q^2}{a^2} = (9.0 \\times 10^9) \\frac{(2.0 \\times 10^{-6})^2}{(0.50)^2} = \\frac{3.6 \\times 10^{-2}}{0.25} = 0.144\\text{ N}$$\n\n"
                                    "**Step 2: Vector addition at $60^\\circ$ angle**\n"
                                    "The angle between the two repulsive force vectors is $\\theta = 60^\\circ$:\n\n"
                                    "$$F_{\\text{net}} = \\sqrt{F_0^2 + F_0^2 + 2 F_0 F_0 \\cos 60^\\circ} = \\sqrt{3} F_0$$\n\n"
                                    "$$F_{\\text{net}} = 1.732 \\times 0.144\\text{ N} \\approx 0.250\\text{ N}$$\n\n"
                                    "**Conclusion:** The net force on each charge has magnitude $0.250\\text{ N}$ directed outward along the bisector of the vertex angle."
                                ),
                            },
                        ],
                    },
                    {
                        "title": "Continuous Charge Distributions and Line Integrals (Draft Preview)",
                        "slug": "continuous-charge-distributions-draft",
                        "summary": "Draft lesson on linear, surface, and volume charge distributions.",
                        "learning_objectives": ["Understand linear charge density lambda"],
                        "estimated_read_time_minutes": 8,
                        "status": ContentStatus.DRAFT.value,
                        "provenance": "Unreviewed author draft — internal testing only.",
                        "is_verified": False,
                        "display_order": 2,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "Linear Charge Density",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": "Draft content: $\\lambda = \\frac{dq}{dl}$.",
                            }
                        ],
                    },
                    {
                        "title": "Electric Field Lines and Gauss's Law Applications (In Review)",
                        "slug": "electric-field-lines-gauss-law-in-review",
                        "summary": "Pending pedagogical review by editorial committee.",
                        "learning_objectives": ["Evaluate electric flux through closed surface"],
                        "estimated_read_time_minutes": 15,
                        "status": ContentStatus.IN_REVIEW.value,
                        "provenance": "Submitted by SME author for review.",
                        "is_verified": False,
                        "display_order": 3,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "Electric Flux Definition",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": "In-review content: $\\Phi = \\oint \\vec{E} \\cdot d\\vec{A}$.",
                            }
                        ],
                    },
                ],
            },
            {
                "topic_number": 2,
                "title": "Electric Dipole and Dipole Moment",
                "slug": "electric-dipole-and-moment",
                "importance_weight": 2,
                "lessons": [
                    {
                        "title": "Electric Dipoles, Dipole Moment, and Torque in External Fields",
                        "slug": "electric-dipoles-torque-in-fields",
                        "summary": "Physical definition of an electric dipole, mathematical dipole moment vector, electric field on axial and equatorial lines, and torque in a uniform electric field.",
                        "learning_objectives": [
                            "Define electric dipole moment vector $\\vec{p} = q (2\\vec{a})$",
                            "Calculate the electric field of a dipole at axial and equatorial points",
                            "Derive the torque $\\vec{\\tau} = \\vec{p} \\times \\vec{E}$ and potential energy $U = -\\vec{p} \\cdot \\vec{E}$ in a uniform electric field",
                        ],
                        "estimated_read_time_minutes": 10,
                        "status": ContentStatus.PUBLISHED.value,
                        "provenance": "Aligned with CBSE Class 12 Physics (NCERT Chapter 1, Section 1.10). Verified by Senior Physics Faculty.",
                        "is_verified": True,
                        "display_order": 1,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "Definition of an Electric Dipole",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "An **electric dipole** is a pair of equal and opposite point charges $+q$ and $-q$ separated by a small distance $2a$.\n\n"
                                    "The **electric dipole moment vector** $\\vec{p}$ is defined as:\n\n"
                                    "$$\\vec{p} = q(2\\vec{a})$$\n\n"
                                    "By international physical convention, the direction of $\\vec{p}$ points from the negative charge $-q$ toward the positive charge $+q$. In SI units, dipole moment is measured in Coulomb-meters ($\\text{C}\\cdot\\text{m}$)."
                                ),
                            },
                            {
                                "section_number": 2,
                                "title": "Axial and Equatorial Electric Fields",
                                "section_type": SectionType.KEY_FORMULA.value,
                                "content_markdown": (
                                    "For a short dipole where the observation distance $r \\gg a$:\n\n"
                                    "### 1. Field on Axial Line (End-on position)\n"
                                    "$${\\vec{E}}_{\\text{axial}} = \\frac{1}{4\\pi\\varepsilon_0} \\frac{2\\vec{p}}{r^3}$$\n\n"
                                    "### 2. Field on Equatorial Line (Broadside-on position)\n"
                                    "$${\\vec{E}}_{\\text{equatorial}} = -\\frac{1}{4\\pi\\varepsilon_0} \\frac{\\vec{p}}{r^3}$$\n\n"
                                    "Notice that for large distances, the axial field magnitude is exactly twice the equatorial field magnitude: $E_{\\text{axial}} = 2 E_{\\text{equatorial}}$."
                                ),
                            },
                            {
                                "section_number": 3,
                                "title": "Torque and Potential Energy in Uniform Electric Field",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "When an electric dipole is placed in a uniform external electric field $\\vec{E}$ at an angle $\\theta$ to the field:\n\n"
                                    "* Net translational force is zero: $\\vec{F}_{\\text{net}} = (+q\\vec{E}) + (-q\\vec{E}) = \\vec{0}$.\n"
                                    "* Net torque $\\vec{\\tau}$ causes the dipole to rotate toward alignment with the field:\n\n"
                                    "$$\\vec{\\tau} = \\vec{p} \\times \\vec{E}, \\quad |\\vec{\\tau}| = p E \\sin\\theta$$\n\n"
                                    "* The electrostatic potential energy stored in the dipole configuration is:\n\n"
                                    "$$U(\\theta) = -\\vec{p} \\cdot \\vec{E} = -p E \\cos\\theta$$"
                                ),
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "board_code": "CBSE",
        "grade_code": "CLASS_12",
        "subject_code": "MATHEMATICS",
        "chapter_number": 1,
        "chapter_title": "Integrals",
        "chapter_slug": "integrals",
        "chapter_summary": "Indefinite and definite integrals, fundamental theorem of calculus, integration techniques, and properties of definite integrals.",
        "topics": [
            {
                "topic_number": 1,
                "title": "Fundamental Theorem of Calculus and Definite Integrals",
                "slug": "fundamental-theorem-calculus",
                "importance_weight": 3,
                "lessons": [
                    {
                        "title": "The Fundamental Theorem of Calculus and Properties of Definite Integrals",
                        "slug": "fundamental-theorem-calculus-and-properties",
                        "summary": "Rigorous treatment of the definite integral as the limit of a Riemann sum, statement of the First and Second Fundamental Theorems, and evaluation of symmetric definite integrals.",
                        "learning_objectives": [
                            "State the First and Second Fundamental Theorems of Calculus",
                            "Evaluate definite integrals using antiderivatives",
                            "Apply standard definite integral properties including $\\int_a^b f(x)dx = \\int_a^b f(a+b-x)dx$",
                        ],
                        "estimated_read_time_minutes": 15,
                        "status": ContentStatus.PUBLISHED.value,
                        "provenance": "Aligned with CBSE Class 12 Mathematics (NCERT Chapter 7, Section 7.7). Verified by Senior Mathematics Faculty.",
                        "is_verified": True,
                        "display_order": 1,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "The Fundamental Theorem of Calculus",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "The Fundamental Theorem of Calculus connects differential calculus and integral calculus in an elegant duality.\n\n"
                                    "### Second Fundamental Theorem of Calculus\n"
                                    "Let $f$ be a continuous function defined on the closed interval $[a, b]$, and let $F$ be any anti-derivative of $f$ such that $F'(x) = f(x)$ for all $x \\in [a, b]$. Then:\n\n"
                                    "$$\\int_{a}^{b} f(x) \\, dx = \\Big[ F(x) \\Big]_{a}^{b} = F(b) - F(a)$$"
                                ),
                            },
                            {
                                "section_number": 2,
                                "title": "Fundamental Properties of Definite Integrals",
                                "section_type": SectionType.KEY_FORMULA.value,
                                "content_markdown": (
                                    "The following standard properties are fundamental for solving examination problems:\n\n"
                                    "1. **Dummy Variable Invariance:** $\\int_{a}^{b} f(x) \\, dx = \\int_{a}^{b} f(t) \\, dt$\n"
                                    "2. **Reversal of Limits:** $\\int_{a}^{b} f(x) \\, dx = -\\int_{b}^{a} f(x) \\, dx$\n"
                                    "3. **Interval Splitting:** $\\int_{a}^{b} f(x) \\, dx = \\int_{a}^{c} f(x) \\, dx + \\int_{c}^{b} f(x) \\, dx$\n"
                                    "4. **King's Property:** $\\int_{a}^{b} f(x) \\, dx = \\int_{a}^{b} f(a + b - x) \\, dx$\n"
                                    "5. **Zero-to-A Formulation:** $\\int_{0}^{a} f(x) \\, dx = \\int_{0}^{a} f(a - x) \\, dx$\n"
                                    "6. **Even / Odd Functions:**\n"
                                    "   $$\\int_{-a}^{a} f(x) \\, dx = \\begin{cases} 2 \\int_{0}^{a} f(x) \\, dx & \\text{if } f(-x) = f(x) \\text{ (even)} \\\\ 0 & \\text{if } f(-x) = -f(x) \\text{ (odd)} \\end{cases}$$"
                                ),
                            },
                            {
                                "section_number": 3,
                                "title": "Worked Example: Applying King's Property",
                                "section_type": SectionType.WORKED_EXAMPLE.value,
                                "content_markdown": (
                                    "**Problem Statement:** Evaluate the integral:\n\n"
                                    "$$I = \\int_{0}^{\\frac{\\pi}{2}} \\frac{\\sin^4 x}{\\sin^4 x + \\cos^4 x} \\, dx$$\n\n"
                                    "**Step 1: Apply King's Property $\\int_0^a f(x)dx = \\int_0^a f(a-x)dx$**\n\n"
                                    "$$I = \\int_{0}^{\\frac{\\pi}{2}} \\frac{\\sin^4(\\frac{\\pi}{2} - x)}{\\sin^4(\\frac{\\pi}{2} - x) + \\cos^4(\\frac{\\pi}{2} - x)} \\, dx$$\n\n"
                                    "Since $\\sin(\\frac{\\pi}{2} - x) = \\cos x$ and $\\cos(\\frac{\\pi}{2} - x) = \\sin x$:\n\n"
                                    "$$I = \\int_{0}^{\\frac{\\pi}{2}} \\frac{\\cos^4 x}{\\cos^4 x + \\sin^4 x} \\, dx$$\n\n"
                                    "**Step 2: Add the two equations**\n\n"
                                    "$$2I = \\int_{0}^{\\frac{\\pi}{2}} \\frac{\\sin^4 x + \\cos^4 x}{\\sin^4 x + \\cos^4 x} \\, dx = \\int_{0}^{\\frac{\\pi}{2}} 1 \\, dx = \\frac{\\pi}{2}$$\n\n"
                                    "$$I = \\frac{\\pi}{4}$$\n\n"
                                    "**Answer:** The value of the integral is $\\frac{\\pi}{4}$."
                                ),
                            },
                        ],
                    }
                ],
            }
        ],
    },
    {
        "board_code": "CBSE",
        "grade_code": "CLASS_12",
        "subject_code": "CHEMISTRY",
        "chapter_number": 1,
        "chapter_title": "Chemical Kinetics",
        "chapter_slug": "chemical-kinetics",
        "chapter_summary": "Rate of chemical reaction, factors affecting rate, rate laws, order and molecularity of reactions, integrated rate equations, and activation energy.",
        "topics": [
            {
                "topic_number": 1,
                "title": "Rate of Reaction, Rate Laws, and Order of Reaction",
                "slug": "rate-of-reaction-and-rate-laws",
                "importance_weight": 2,
                "lessons": [
                    {
                        "title": "Rate of Chemical Reaction, Differential Rate Laws, and Order vs. Molecularity",
                        "slug": "rate-of-reaction-differential-rate-laws",
                        "summary": "Concepts of average and instantaneous reaction rates, stoichiometric rate expressions, experimental rate laws, and key differences between order and molecularity.",
                        "learning_objectives": [
                            "Express reaction rates in terms of stoichiometric disappearance of reactants and appearance of products",
                            "Deduce rate laws and rate constant units for zero, first, and second order reactions",
                            "Differentiate clearly between reaction order (experimental) and molecularity (theoretical)",
                        ],
                        "estimated_read_time_minutes": 11,
                        "status": ContentStatus.PUBLISHED.value,
                        "provenance": "Aligned with CBSE Class 12 Chemistry (NCERT Chapter 4, Section 4.1 & 4.2). Verified by Senior Chemistry Faculty.",
                        "is_verified": True,
                        "display_order": 1,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "Definition of Chemical Reaction Rate",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "The **rate of a chemical reaction** is defined as the change in the concentration of any one of its reactants or products per unit time.\n\n"
                                    "For a general stoichiometric reaction:\n\n"
                                    "$$aA + bB \\longrightarrow cC + dD$$\n\n"
                                    "The instantaneous reaction rate is expressed unambiguously by dividing by the stoichiometric coefficients:\n\n"
                                    "$$\\text{Rate} = -\\frac{1}{a} \\frac{d[A]}{dt} = -\\frac{1}{b} \\frac{d[B]}{dt} = +\\frac{1}{c} \\frac{d[C]}{dt} = +\\frac{1}{d} \\frac{d[D]}{dt}$$\n\n"
                                    "The negative signs indicate consumption of reactants, ensuring the overall reaction rate is always a positive quantity."
                                ),
                            },
                            {
                                "section_number": 2,
                                "title": "Rate Law and Reaction Order",
                                "section_type": SectionType.KEY_FORMULA.value,
                                "content_markdown": (
                                    "The **rate law** is an experimentally determined mathematical expression relating the reaction rate to the molar concentrations of reactants:\n\n"
                                    "$$\\text{Rate} = k [A]^x [B]^y$$\n\n"
                                    "* $k$ is the **rate constant** (or specific reaction rate).\n"
                                    "* $x$ and $y$ are the partial orders with respect to reactants $A$ and $B$.\n"
                                    "* The **overall order of reaction** is $n = x + y$.\n\n"
                                    "**Crucial Rule:** The exponents $x$ and $y$ cannot be predicted from the balanced stoichiometric equation; they must be determined experimentally."
                                ),
                            },
                            {
                                "section_number": 3,
                                "title": "Comparison: Order vs. Molecularity",
                                "section_type": SectionType.NOTE.value,
                                "content_markdown": (
                                    "| Feature | Order of Reaction | Molecularity of Reaction |\n"
                                    "| :--- | :--- | :--- |\n"
                                    "| **Definition** | Sum of powers of concentration terms in the rate law. | Number of reacting species taking part in an elementary step. |\n"
                                    "| **Determination** | Purely experimental quantity. | Theoretical concept deduced from mechanism. |\n"
                                    "| **Values** | Can be zero, fractional, or integer ($0, 1/2, 1, 2, \\dots$). | Must be a positive integer ($1, 2, 3$). Cannot be zero or fractional. |\n"
                                    "| **Complex Reactions** | Applicable to both elementary and complex reactions. | Has no physical meaning for overall complex reactions (only defined per elementary step). |"
                                ),
                            },
                        ],
                    }
                ],
            }
        ],
    },
    {
        "board_code": "ENG_UNIV",
        "grade_code": "SEM_1_2",
        "subject_code": "ENG_CS101",
        "chapter_number": 1,
        "chapter_title": "Pointers, Memory Architecture and Dynamic Allocation",
        "chapter_slug": "pointers-and-dynamic-memory-allocation",
        "chapter_summary": "Low-level memory architecture in C: stack vs heap, pointer arithmetic, dynamic allocation with malloc/free, and memory leak prevention.",
        "topics": [
            {
                "topic_number": 1,
                "title": "Pointers and Dynamic Memory Allocation in C",
                "slug": "pointers-dynamic-memory-c",
                "importance_weight": 3,
                "lessons": [
                    {
                        "title": "Memory Architecture, Pointer Arithmetic, and Heap Management in C",
                        "slug": "memory-architecture-pointer-arithmetic-c",
                        "summary": "Master pointer fundamentals, direct memory addressing, pointer arithmetic, void pointers, malloc, calloc, realloc, and defensive deallocation.",
                        "learning_objectives": [
                            "Understand the C memory layout: Text, Data, BSS, Heap, and Stack segments",
                            "Manipulate memory addresses directly using pointer variables and dereference operators (* and &)",
                            "Allocate and resize memory on the heap safely using malloc(), calloc(), and realloc()",
                            "Identify and prevent dangling pointers, double-free vulnerabilities, and memory leaks",
                        ],
                        "estimated_read_time_minutes": 14,
                        "status": ContentStatus.PUBLISHED.value,
                        "provenance": "Aligned with AICTE Model Engineering Curriculum (CS101: Programming for Problem Solving). Verified by CS Faculty.",
                        "is_verified": True,
                        "display_order": 1,
                        "sections": [
                            {
                                "section_number": 1,
                                "title": "The C Process Address Space: Stack vs. Heap",
                                "section_type": SectionType.CONCEPT.value,
                                "content_markdown": (
                                    "When an operating system executes a C program, it allocates a contiguous virtual address space partitioned into distinct segments:\n\n"
                                    "1. **Text Segment (Code):** Contains executable machine instructions. It is read-only to prevent accidental modification.\n"
                                    "2. **Initialized Data (.data) & Uninitialized Data (.bss):** Stores global and static variables.\n"
                                    "3. **The Heap:** Region utilized for dynamic memory allocation at runtime via `malloc()`. It grows upwards toward higher memory addresses.\n"
                                    "4. **The Stack:** Region storing local variables, function parameters, and return addresses. It grows downward toward lower memory addresses with automatic allocation and cleanup upon function return.\n\n"
                                    "A **pointer** is a variable that stores the memory address of another variable. If variable `x` resides at address `0x7ffee4b2a`, an integer pointer `int *p = &x;` stores that exact address."
                                ),
                            },
                            {
                                "section_number": 2,
                                "title": "Pointer Arithmetic and Array Subscript Equivalence",
                                "section_type": SectionType.WORKED_EXAMPLE.value,
                                "content_markdown": (
                                    "In C, arithmetic operations on pointers are automatically scaled by the size of the underlying data type:\n\n"
                                    "$$\\text{address}(p + i) = \\text{address}(p) + (i \\times \\text{sizeof}(*p))$$\n\n"
                                    "For example, if `p` is an `int *` on an architecture where `sizeof(int) == 4`, advancing `p + 1` increases the address value by exactly 4 bytes.\n\n"
                                    "### Array-Pointer Duality\n"
                                    "In expression contexts, an array identifier decays into a pointer to its first element:\n\n"
                                    "```c\n"
                                    "int arr[5] = {10, 20, 30, 40, 50};\n"
                                    "int *ptr = arr; // equivalent to &arr[0]\n"
                                    "// Array indexing is syntactic sugar for pointer arithmetic:\n"
                                    "// arr[i] == *(arr + i) == *(i + arr) == i[arr]\n"
                                    "```"
                                ),
                            },
                            {
                                "section_number": 3,
                                "title": "Dynamic Heap Management & Defensive Memory Hygiene",
                                "section_type": SectionType.NOTE.value,
                                "content_markdown": (
                                    "Dynamic allocation allows memory requests whose sizes are determined at runtime:\n\n"
                                    "* `malloc(size_t bytes)`: Allocates uninitialized memory. Returns `NULL` if allocation fails.\n"
                                    "* `calloc(size_t num, size_t size)`: Allocates contiguous elements initialized to zero.\n"
                                    "* `free(void *ptr)`: Releases heap memory back to the allocator.\n\n"
                                    "**Defensive Rule:** Always verify that `malloc` did not return `NULL`, and set pointers to `NULL` immediately after freeing:\n\n"
                                    "```c\n"
                                    "int *buffer = (int *)malloc(100 * sizeof(int));\n"
                                    "if (!buffer) {\n"
                                    "    perror(\"Memory allocation failed\");\n"
                                    "    exit(EXIT_FAILURE);\n"
                                    "}\n"
                                    "// ... use buffer ...\n"
                                    "free(buffer);\n"
                                    "buffer = NULL; // Prevents dangling pointer dereferencing\n"
                                    "```"
                                ),
                            },
                        ],
                    }
                ],
            }
        ],
    },
]


async def seed_academic_content(session: AsyncSession) -> None:
    """Populate sample academic chapters, topics, lessons, and sections idempotently."""
    for item in SAMPLE_LESSONS_DATA:
        # Find Curriculum
        board_res = await session.execute(
            select(BoardCurriculum).where(BoardCurriculum.code == item["board_code"])
        )
        board = board_res.scalar_one_or_none()
        if not board:
            continue

        # Find Grade Stage
        grade_res = await session.execute(
            select(GradeStage).where(
                GradeStage.board_id == board.id,
                GradeStage.code == item["grade_code"],
            )
        )
        grade = grade_res.scalar_one_or_none()
        if not grade:
            continue

        # Find Subject
        sub_res = await session.execute(
            select(Subject).where(
                Subject.grade_stage_id == grade.id,
                Subject.code == item["subject_code"],
            )
        )
        subject = sub_res.scalar_one_or_none()
        if not subject:
            continue

        # Find or create Chapter
        chap_res = await session.execute(
            select(Chapter).where(
                Chapter.subject_id == subject.id,
                Chapter.chapter_number == item["chapter_number"],
            )
        )
        chapter = chap_res.scalar_one_or_none()
        if not chapter:
            chapter = Chapter(
                subject_id=subject.id,
                chapter_number=item["chapter_number"],
                title=item["chapter_title"],
                slug=item["chapter_slug"],
                summary=item["chapter_summary"],
                display_order=item["chapter_number"],
            )
            session.add(chapter)
            await session.flush()

        # Seed Topics
        for top_data in item["topics"]:
            top_res = await session.execute(
                select(Topic).where(
                    Topic.chapter_id == chapter.id,
                    Topic.topic_number == top_data["topic_number"],
                )
            )
            topic = top_res.scalar_one_or_none()
            if not topic:
                topic = Topic(
                    chapter_id=chapter.id,
                    topic_number=top_data["topic_number"],
                    title=top_data["title"],
                    slug=top_data["slug"],
                    importance_weight=top_data["importance_weight"],
                    display_order=top_data["topic_number"],
                )
                session.add(topic)
                await session.flush()

            # Seed Lessons
            for les_data in top_data["lessons"]:
                les_res = await session.execute(
                    select(Lesson).where(
                        Lesson.topic_id == topic.id,
                        Lesson.slug == les_data["slug"],
                    )
                )
                lesson = les_res.scalar_one_or_none()
                if not lesson:
                    lesson = Lesson(
                        topic_id=topic.id,
                        title=les_data["title"],
                        slug=les_data["slug"],
                        summary=les_data["summary"],
                        learning_objectives=les_data.get("learning_objectives", []),
                        estimated_read_time_minutes=les_data["estimated_read_time_minutes"],
                        status=les_data["status"],
                        display_order=les_data["display_order"],
                        provenance=les_data.get("provenance"),
                        is_verified=les_data.get("is_verified", False),
                    )
                    session.add(lesson)
                    await session.flush()

                    # Seed Sections
                    for sec_data in les_data.get("sections", []):
                        sec = LessonSection(
                            lesson_id=lesson.id,
                            section_number=sec_data["section_number"],
                            title=sec_data["title"],
                            content_markdown=sec_data["content_markdown"],
                            section_type=sec_data["section_type"],
                            display_order=sec_data["section_number"],
                        )
                        session.add(sec)

    await session.commit()
    logger.info("Academic content and structured lessons seed completed successfully.")
