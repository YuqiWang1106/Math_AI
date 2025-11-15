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
  const [showIncompleteModal, setShowIncompleteModal] = useState(false);
  const [pendingPayload, setPendingPayload] = useState(null);

  // Handle Knowledge Dimension Input Change
  const handleChangeKT = (index, field, value) => {
    const updated = [...knowledgeTypes];
    updated[index][field] = value;
    setKnowledgeTypes(updated);
  };

  const hasEmptyRequiredFields = () => {
    if (!studentId.trim()) return true;
    if (!problem.trim()) return true;
    // 这里只把 examples 当作必填项，uncertainties 仍然视为可选
    if (knowledgeTypes.some((kt) => !kt.examples.trim())) return true;
    return false;
  };

  const proceedToChat = (payload) => {
    localStorage.setItem("assessmentData", JSON.stringify(payload));
    navigate("/chat");
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

    if (hasEmptyRequiredFields()) {
      setPendingPayload(payload);
      setShowIncompleteModal(true);
      return;
    }

    proceedToChat(payload);
  };

  const handleContinueAnyway = () => {
    if (pendingPayload) {
      proceedToChat(pendingPayload);
      setPendingPayload(null);
      setShowIncompleteModal(false);
    }
  };

  const handleBackToEdit = () => {
    setShowIncompleteModal(false);
    setPendingPayload(null);
  };

  return (
    <div className="container-fluid">
      <div className="row nav-part">
        Health Chatbot
      </div>

      <div className="row main-content-part">
        <div className="col-5 left-side">
                        <p>
I want to teach you to assess your own knowledge that you have about a health affliction and how to determine if this is impacting YOU and what to do about it. Suppose you wanted to assess your own knowledge about colds. If I want to be able to assess my knowledge about health conditions, I need four types of knowledge. These are facts, strategies, procedures and rationales. Facts are concepts or definitions you have to describe objects or elements. For example, in the case of a common cold, I would need to know what exactly colds are, how they spread, when symptoms typically appear, how they impact different age groups, and how long colds typically last. Strategies are general processes I would use to cure a cold or alleviate its symptoms. For colds, this would be things like resting, drinking plenty of fluids, hygiene, etc. Procedures are specific steps that you would use in processes or the strategies said earlier (think of them like mini-building blocks that make up strategies). So, in the example of hygiene, this would be things like washing your hands, avoiding close contact with people, properly disposing of things like used tissues, sneezing into your elbow, etc. Finally, I need to know the rationales, or the reasons why strategies and procedures work the way that they do. In the example of hygiene, this could be that the procedures above like washing your hands and avoiding close contact help to stop the spread of germs which could make you sick and give you a cold. Or, resting reduces the body’s need to use its resources for other things and frees up resources for the body to use to fight the cold. Think of facts as the “what”, strategies and procedures as the “how” and rationales as the “why”.
            </p>
            <p>
              <strong>For facts</strong>, I know that the cause of the common cold is viruses like rhinoviruses, coronaviruses, and adenoviruses. You know that colds spread through coughing and sneezing, but they also spread through touching contaminated surfaces, which is common to forget. I remembered that symptoms usually appear a few days after exposure, but forgot the specific number of days (typically 1-3 days). I know that most colds last about 7-10 days, though I didn’t realize mild symptoms can linger for up to 2 weeks. Things you don’t know: Are there any supplements/vitamins that could help me fight this cold? Can I still exercise when I have this cold? What is the point at which I am no longer contagious and can continue doing normal things?
            </p>
            <p>
              <strong>For strategies</strong>, I know that you can rest and allow your body to heal, drink warm liquids such as herbal teas and warm water, stay very hygienic (sanitize and wash hands frequently) , and you should isolate yourself to prevent spreading the cold to others. Things I don’t know: Are there things I can do to reduce my symptoms/suffering while I’m healing?
            </p>
            <p>
              <strong>For procedures</strong>, I know that you can monitor your temperature daily to see if your health is getting better and identify things that would need medical attention such as a high fever or difficulty breathing. I know I should drink a lot of fluids. Things I don’t know: Are there any fluids that I might drink that might actually just be making me more dehydrated? Is it better to take my temperature on my tongue, forehead, armpit, etc.?

            </p>
            <p>
              <strong>For rationales</strong>, I know that resting allows your immune system to focus on the energy fighting the cold, hydration keeps the mucous membranes moist, monitoring ear pain helps differentiate between cold and ear infection. Things I don’t know: I kind of forgot how exactly humidifiers work, although I recognize they help cure/prevent colds. Why does it take a few days before cold symptoms begin to appear? Why do I get so much congestion when I have a cold?
            </p>
            <p>
After writing whatever you know for each of these points, look over what you have written to see which points you know, what you possibly got wrong, which points you did not know at all, etc. Then add what you do know and what you think you are still missing based on your self-assessment. When I look over what I wrote, I see that I am generally good with facts, but may have forgotten some specifics like how long it takes before symptoms show up, additional things I could do (like supplements/vitamins), when it is okay to continue doing normal activities, etc. For strategies, I can see that I’m generally good at remembering effective strategies for preventing and recovering from colds. I realize that I don’t know how to reduce symptoms while healing, so that is a point that I need to do some more research on. For procedures, I see that I’m good at remembering specific procedures to implement strategies. I realize that I don’t know which place is best to use to measure temperature and if there are any fluids I should actually avoid drinking. For rationales, I can see that I’m generally good but I did forget how humidifiers work. I don’t know why it takes a while before symptoms appear and why I get as much congestion as I do, so that is something I need to look into further. Using those gaps in the writing that I did earlier, I can do some research to find out the things I didn’t know earlier. For example, I can do research to find out that humidifiers work to cure/prevent colds by preventing the airway from drying out, as that can worsen coughing and irritation. 
            </p>
            <p>
Use the above example of a self-assessment for colds and complete one for yourself on what you know about stress and how it affects people. Be sure to include facts, strategies, procedures, and rationales. Once you are done, review your self-assessed knowledge and summarize what things you know and don’t know. Then use our health chatbot to help you fill in the gaps of what you don’t know and to learn more things about stress.

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

      {showIncompleteModal && (
        <div className="incomplete-modal-backdrop">
          <div className="incomplete-modal">
            <h3 className="incomplete-modal-title">Incomplete self-assessment</h3>
            <p className="incomplete-modal-text">
              We noticed that some parts of your self-assessment are still empty.
              We <strong>recommend</strong> filling in as much as you can so the
              chatbot can give more helpful guidance.
            </p>
            <p className="incomplete-modal-text">
              You can go back to add more details, or continue to the chat anyway.
            </p>
            <div className="incomplete-modal-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleBackToEdit}
              >
                Go back
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleContinueAnyway}
              >
                Continue anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Template_Page;
