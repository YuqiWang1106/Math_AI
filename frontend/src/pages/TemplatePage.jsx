import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import '../css/TemplatePage.css';

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
I want to teach you to assess your own knowledge that you have about a health affliction and how to determine if this is impacting YOU and what to do about it. 
Suppose you wanted to assess your own knowledge about colds. If I want to be able to solve problems like these, I need four types of knowledge. 
These are facts, strategies, procedures and rationales. 
Facts are concepts you have to describe objects or elements. 
For example, in the case of a common cold, I would need to know what exactly colds are, how they spread, when symptoms typically appear, how they impact different age groups, and how long colds typically last. 
Strategies are general processes I would use to cure a cold or alleviate its symptoms. For colds, this would be things like resting, drinking plenty of fluids, hygiene, etc. 
Procedures are specific steps that you would use in processes or the strategies said earlier (think of them like mini-building blocks that make up strategies). 
So, in the example of hygiene, this would be things like washing your hands, avoiding close contact with people, properly disposing of things like used tissues, sneezing into your elbow, etc. 
Finally, I need to know the rationales, or the reasons why strategies and procedures work the way that they do. 
In the example of hygiene, this could be that the procedures above like washing your hands and avoiding close contact help to stop the spread of germs which could make you sick and give you a cold. 
Think of facts as the “what”, strategies and procedures as the “how” and rationales as the “why”.

Keeping these things in mind, this is how I might assess my own knowledge on colds. 
Practice writing what you know about each of these things (facts, strategies, procedures, and rationales) to figure out where your personal strong points are and which points need more work. 
Let’s practice together using the example of colds.

            </p>
            <p>
              <strong>For facts</strong>, I know that the cause of the common cold is viruses like rhinoviruses, coronaviruses, and adenoviruses. 
              You know that colds spread through coughing and sneezing, but they also spread through touching contaminated surfaces, which is common to forget. 
              I remembered that symptoms usually appear a few days after exposure, but forgot the specific number of days (typically 1-3 days). 
              I know that most colds last about 7-10 days, though I didn’t realize mild symptoms can linger for up to 2 weeks.

            </p>
            <p>
              <strong>For strategies</strong>, I know that you can rest and allow your body to heal, drink warm liquids such as herbal teas and warm water, stay very hygienic (sanitize and wash hands frequently) , and you should isolate yourself to prevent spreading the cold to others.

            </p>
            <p>
              <strong>For procedures</strong>, I know that you can monitor your temperature daily to see if your health is getting better and identify things that would need medical attention such as a high fever or difficulty breathing.

            </p>
            <p>
              <strong>For rationales</strong>, I know that resting allows your immune system to focus on the energy fighting the cold, hydration keeps the mucous membranes moist, monitoring ear pain helps differentiate between cold and ear infection. I kind of forgot how exactly humidifiers work, although I recognize they help cure/prevent colds.

            </p>
            <p>
After writing whatever you know for each of these points, look over what you have written to see which points you know, what you possibly got wrong, which points you did not know at all, etc. 
Then add what you do know and what you think you are still missing based on your self-assessment.
When I look over what I wrote, I see that I am generally good with facts, but may have forgotten some specifics like how long it takes before symptoms show up. 
For strategies, I can see that I’m generally good at remembering effective strategies for preventing and recovering from colds. 
For procedures, I see that I’m good at remembering specific procedures to implement strategies. 
For rationales, I can see that I’m generally good but I did forget how humidifiers work. 
Using that gap in the writing that I did earlier, I can do some research to find out that humidifiers work to cure/prevent colds by preventing the airway from drying out, as that can worsen coughing and irritation.
            </p>
        </div>

        <div className="col-5 right-side">
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
