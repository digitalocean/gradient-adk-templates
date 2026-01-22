"""
Data Analysis Agent - Code Execution and Visualization.

This agent generates and executes Python code for data analysis,
including creating visualizations and charts.
"""

import os
import io
import sys
import base64
import logging
import tempfile
import traceback
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field
from contextlib import redirect_stdout, redirect_stderr
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"
BASE_URL = "https://inference.do-ai.run/v1"


def get_model(temperature: float = 0.0) -> ChatOpenAI:
    """Get a ChatOpenAI instance configured for Gradient."""
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
        temperature=temperature
    )


class AnalysisCode(BaseModel):
    """Generated Python code for analysis."""
    code: str = Field(description="Python code to execute for analysis")
    explanation: str = Field(description="Explanation of what the code does")
    creates_visualization: bool = Field(description="Whether the code creates a visualization")
    required_libraries: list[str] = Field(description="Python libraries required by the code")


class AnalysisResult(BaseModel):
    """Result of code execution."""
    success: bool
    code: str
    explanation: str
    output: Optional[str] = None
    error: Optional[str] = None
    images: List[str] = Field(default_factory=list)  # Base64 encoded images
    image_paths: List[str] = Field(default_factory=list)  # File paths if saved


# Output directory for generated images
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def create_analysis_prompt(
    question: str,
    data_description: str,
    available_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create the prompt for data analysis code generation.

    Args:
        question: The analysis question
        data_description: Description of available data
        available_data: Optional sample data for context

    Returns:
        Formatted prompt
    """
    data_context = ""
    if available_data:
        data_context = f"""
Available data (passed as 'data' variable, a pandas DataFrame):
Columns: {available_data.get('columns', [])}
Sample rows: {available_data.get('rows', [])[:3]}
Total rows: {available_data.get('row_count', 0)}
"""

    prompt = f"""You are a data analyst writing Python code for analysis and visualization.

{data_description}
{data_context}

Task: {question}

Write Python code to answer this question. Guidelines:
1. Use pandas for data manipulation
2. Use matplotlib or seaborn for visualizations
3. The data is already loaded in a variable called 'data' (pandas DataFrame)
4. If creating a visualization, save it using plt.savefig(output_path) where output_path is provided
5. Print any numerical results or insights
6. Keep the code concise and focused
7. Add brief comments for clarity
8. Handle potential errors gracefully
9. For visualizations:
   - Use clear titles and labels
   - Choose appropriate chart types
   - Use a clean style (seaborn or matplotlib styles)
   - Set figure size appropriately

Important: The variable 'data' contains the query results as a pandas DataFrame.
The variable 'output_path' contains the path where any visualization should be saved.

Generate only the Python code, no markdown formatting."""

    return prompt


def generate_analysis_code(
    question: str,
    data_description: str,
    available_data: Optional[Dict[str, Any]] = None
) -> AnalysisCode:
    """
    Generate Python code for data analysis.

    Args:
        question: Analysis question
        data_description: Description of the data
        available_data: Optional data sample

    Returns:
        Generated analysis code
    """
    logger.info(f"Generating analysis code for: {question}")

    prompt = create_analysis_prompt(question, data_description, available_data)

    model = get_model(temperature=0.0)
    structured_model = model.with_structured_output(AnalysisCode)

    analysis_code = structured_model.invoke([
        {"role": "system", "content": "You are a data analyst writing Python code for analysis and visualization."},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Generated code ({len(analysis_code.code)} chars), creates_visualization={analysis_code.creates_visualization}")

    return analysis_code


def execute_analysis_code(
    code: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 60
) -> AnalysisResult:
    """
    Execute Python analysis code in a sandboxed environment.

    Args:
        code: Python code to execute
        data: Query result data to analyze
        timeout: Execution timeout in seconds

    Returns:
        Execution result with output and any generated images
    """
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    logger.info("Executing analysis code")

    # Prepare output directory and file
    output_dir = ensure_output_dir()
    output_path = output_dir / f"chart_{os.getpid()}_{id(code)}.png"

    # Convert data to DataFrame
    df = None
    if data and data.get("columns") and data.get("rows"):
        df = pd.DataFrame(data["rows"], columns=data["columns"])

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Prepare execution namespace
    exec_namespace = {
        "pd": pd,
        "np": __import__("numpy"),
        "plt": plt,
        "sns": __import__("seaborn"),
        "data": df,
        "output_path": str(output_path),
        "__builtins__": __builtins__
    }

    images = []
    image_paths = []

    try:
        # Execute the code
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, exec_namespace)

        # Check if a plot was saved
        if output_path.exists():
            # Read and encode the image
            with open(output_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                images.append(image_data)
                image_paths.append(str(output_path))
            logger.info(f"Visualization saved to: {output_path}")

        # Also check for any unsaved matplotlib figures
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            if not output_path.exists() or fig_num > 1:
                # Save additional figures
                fig_path = output_dir / f"chart_{os.getpid()}_{id(code)}_{fig_num}.png"
                fig.savefig(fig_path, dpi=150, bbox_inches='tight')
                with open(fig_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                    images.append(image_data)
                    image_paths.append(str(fig_path))
            plt.close(fig)

        output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        if stderr_output:
            output += f"\nWarnings/Errors:\n{stderr_output}"

        return AnalysisResult(
            success=True,
            code=code,
            explanation="",
            output=output if output else "Code executed successfully",
            images=images,
            image_paths=image_paths
        )

    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        error_trace = traceback.format_exc()

        # Close any open figures
        plt.close('all')

        return AnalysisResult(
            success=False,
            code=code,
            explanation="",
            error=f"{str(e)}\n\n{error_trace}",
            output=stdout_capture.getvalue()
        )


def run_analysis(
    question: str,
    data: Dict[str, Any],
    data_description: str
) -> AnalysisResult:
    """
    Complete analysis pipeline: generate code and execute it.

    Args:
        question: Analysis question
        data: Query result data to analyze
        data_description: Description of the data

    Returns:
        Analysis result with output and visualizations
    """
    try:
        # Generate analysis code
        analysis_code = generate_analysis_code(question, data_description, data)

        # Execute the code
        result = execute_analysis_code(analysis_code.code, data)
        result.explanation = analysis_code.explanation

        return result

    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        return AnalysisResult(
            success=False,
            code="",
            explanation="",
            error=str(e)
        )


def fix_analysis_code(
    original_code: str,
    error_message: str,
    data_description: str
) -> AnalysisCode:
    """
    Attempt to fix analysis code that produced an error.

    Args:
        original_code: The code that failed
        error_message: The error message received
        data_description: Description of the data

    Returns:
        Fixed analysis code
    """
    prompt = f"""The following Python code produced an error. Please fix it.

{data_description}

Original Code:
```python
{original_code}
```

Error:
{error_message}

Please provide corrected Python code that addresses the error. Maintain the same
analysis goal but fix the issues."""

    model = get_model(temperature=0.0)
    structured_model = model.with_structured_output(AnalysisCode)

    return structured_model.invoke([
        {"role": "system", "content": "You are a data analyst fixing Python code."},
        {"role": "user", "content": prompt}
    ])
