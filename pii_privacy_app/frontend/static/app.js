const $ = s => document.querySelector(s);
$("#go").onclick = () => {
  const txt = $("#in").value.trim();
  if(!txt){alert("Enter text");return;}
  fetch("/api/process_text",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({text:txt})
  })
  .then(r=>r.json()).then(d=>{
      $("#out").style.display="block";
      $("#corrected").textContent = d.corrected_text;
      $("#colored").innerHTML     = d.colored_text;
      $("#masked").textContent    = d.masked_text;
      $("#answer").textContent    = d.llm_response;
  });
};

// tab switch
document.querySelectorAll(".tab").forEach(btn=>{
  btn.onclick = ()=>{
    document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
    document.querySelectorAll(".pane").forEach(p=>p.style.display="none");
    btn.classList.add("active");
    $("#"+btn.dataset.t).style.display="block";
  };
});