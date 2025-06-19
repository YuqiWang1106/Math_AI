import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Template_Page() {
  const navigate = useNavigate();

  const [studentId, setStudentId] = useState("");
  const [problem, setProblem] = useState("");
  const [knowledgeTypes, setKnowledgeTypes] = useState([
    { type: "facts", examples: "", uncertainties: "" },
    { type: "strategies", examples: "", uncertainties: "" },
    { type: "procedures", examples: "", uncertainties: "" },
    { type: "rationales", examples: "", uncertainties: "" },
  ]);

  // Handle Knowledge Dimension Input Change
  const handleChangeKT = (index, field, value) => {
    const updated = [...knowledgeTypes];
    updated[index][field] = value;
    setKnowledgeTypes(updated);
  };

  const handleSubmit = async () => {
    const payload = {
      student_id: studentId,
      json_data: {
        self_assessment: {
          problem,
          knowledge_types: knowledgeTypes,
        },
      },
    };
    // Store in local storage
    localStorage.setItem("assessmentData", JSON.stringify(payload));
    navigate("/chat");
  };

  return (
    <div className="container-fluid">
      <div className="row nav-part">
        This is navbar.
      </div>

      <div className="row main-content-part">
        <div className="col-5 left-side">
                        <p>
              I want to teach you how to assess your own knowledge that you have
              about a subject area. Let’s do this by taking an example that you
              already know. Suppose you wanted to assess your own knowledge
              about solving 2-step equations of the form ax + b = c. An example
              of this type of problem is 2x + 3 = 15. If I want to be able to
              solve problems like these, I need four types of knowledge. These
              are facts, strategies, procedures and rationales. Fact are
              concepts you have that describe objects or elements. For example,
              for two step equations, I need to know what variables, constants,
              coefficients, equations, and expressions are. Strategies are
              general processes I would use to solve a problem. For two step
              equations, this would be reverse order of operations. Procedures
              are the specific steps that I would use in a strategy. So if I am
              using reverse order of operations, I need to know additive and
              multiplicative inverses. Finally, I need to know rationales which
              are the reasons why the strategies or the procedures work the way
              they do. For example, this could include things like the
              subtraction or the division property of equality that says that
              when you do the same operation to both sides of an equation, you
              preserve the value of the equation. You can think of facts as
              telling you “what”, strategies and procedures as telling you “how”
              and rationales as telling you “why”. With this in mind, this is
              how I might assess my own knowledge of solving two step equations.
            </p>
            <p>
              <strong>For facts</strong>, I need to know what variables,
              constants, coefficients, equations and expressions are. A variable
              is an unknown quantity, usually represented by a letter. A
              constant is a specific number. A coefficient is a number that you
              multiply a variable by like 2x. An equation is an expression that
              is equally to another expression and the two expressions are
              joined by an equal sign. An expression is one or more terms that
              are combined by mathematical operations like addition,
              subtraction, multiplication and division.
            </p>
            <p>
              <strong>For strategies</strong>, I need to know reverse order of
              operations which is SADMEP. This stands for subtraction, addition,
              division, multiplication, exponents and parentheses. I know that
              I’m supposed to do these in order but I don’t remember whether I’m
              supposed to do subtraction always before addition or just which
              one goes first. The same is true for division and multiplication.
            </p>
            <p>
              <strong>For procedures</strong>, I need to know additive inverse
              and multiplicative inverse. The additive inverse is taking the
              number with the opposite sign as the constant and adding it to
              both sides of the equation. The multiplicative inverse is taking
              the inverse of the coefficient of the variable and multiplying
              both sides of the equation by it. However, if the coefficient is
              negative, I’m not sure if the multiplicative inverse is supposed
              to be negative as well.
            </p>
            <p>
              <strong>For rationales</strong>, I believe the two rationales I
              need are the subtraction property of equality and the division
              property of equality. The subtraction property of equality says
              that if I subtract the same number from both sides, which is what
              I’m doing with the additive inverse, I preserve the equality.
              Similarly, the division property of equality says that if I divide
              both sides of the equation by the same number, which is what I’m
              doing with the multiplicative inverse, I preserve the equality.
            </p>
            <p>
              When I look over what I wrote, I see that I am good with my facts.
              On my strategy, I’m not sure about the order of steps in reverse
              order of operations when it comes to subtraction and addition or
              multiplication and division, so I need to learn those. On
              procedures, I’m not sure what to do with multiplicative inverses
              when the coefficient is negative, so I need to learn that as well.
              For rationales, I think I’m OK. I don’t think I have any missing
              facts/concepts that I left out that I should know or I didn’t list
              any facts/concepts where I didn’t know what they were. For the
              strategy, I believe I listed the correct strategy and parts of the
              strategy, but I wasn’t sure about some of the ordering of steps in
              the strategy. For procedures, I was good on the additive inverse
              but had a question on carrying out the multiplicative inverse when
              the coeffcient was negative. For rationales, I think I had all the
              rationales that were important and that I understood them as well.
              I don’t think I left anything out.
            </p>
        </div>

        <div className="col right-side">
          <h3>Self Assessment</h3>

          <div className="mb-3">
            <label>Student ID</label>
            <input type="text" className="form-control" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
          </div>

          <div className="mb-3">
            <label>Problem</label>
            <textarea className="form-control" value={problem} onChange={(e) => setProblem(e.target.value)} />
          </div>

          {/* Dynamically render input area */}
          {knowledgeTypes.map((kt, i) => (
            <div key={i} className="mb-3">
              <label>{kt.type.charAt(0).toUpperCase() + kt.type.slice(1)}</label>
              <textarea
                className="form-control"
                placeholder="Examples"
                value={kt.examples}
                onChange={(e) => handleChangeKT(i, "examples", e.target.value)}
              />
              <textarea
                className="form-control mt-1"
                placeholder="Uncertainties (optional)"
                value={kt.uncertainties}
                onChange={(e) => handleChangeKT(i, "uncertainties", e.target.value)}
              />
            </div>
          ))}

          <div className="text-end">
            <button className="btn btn-primary submit" onClick={handleSubmit}>
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Template_Page;
