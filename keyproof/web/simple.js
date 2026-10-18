// Shared helpers for the simple tenant and landlord screens: server calls, language, plain-word labels.
(function () {
  const S = {};
  S.api = async (path, body) => {
    const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.statusText);
    return j;
  };
  S.esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  S.eur = (n) => "€" + Number(n || 0).toLocaleString("en-US");
  const amt = (n) => (Number(n) > 0 ? S.eur(n) : "€ …");
  S.$ = (id) => document.getElementById(id);

  // ---- language
  let lang = "en";
  try { lang = localStorage.getItem("kp-lang") || (navigator.language || "en").slice(0, 2); } catch (e) { /* storage blocked */ }
  if (!["en", "it", "tr"].includes(lang)) lang = "en";
  S.lang = () => lang;
  S.setLang = (l) => { lang = l; try { localStorage.setItem("kp-lang", l); } catch (e) { /* ignore */ } document.documentElement.lang = l; };
  document.documentElement.lang = lang;

  const T = {
    en: {
      tenant: "Tenant", landlord: "Landlord", step: "Step {a} of {b}",
      t_wait_title: "Waiting for a landlord", t_wait_text: "When a landlord publishes what they need, it appears here.",
      t1_title: "The landlord would like to know", t1_next: "Continue",
      t2_title: "Add your official documents", t2_text: "Only documents signed by your bank, your municipality, your university or your employer are accepted. They stay on this computer.",
      choose: "Choose file", use_demo: "Use demo document", try_fake: "Try a changed document (demo)",
      missing: "Not added yet", original: "Original, signed by {issuer}", refused: "Not accepted",
      t2_next: "All documents added – continue",
      t3_title: "Create your private proof", t3_text: "Your computer checks your documents against the landlord's rules and creates a proof. The proof says only “yes” for each rule – no names, no amounts, no documents.",
      make_proof: "Create my private proof", proving: "Working… this takes about 10 seconds",
      proof_ready: "Your proof is ready", proof_none: "A proof can't be made: at least one rule is not met.",
      send: "Send to the landlord", send_q: "Send your proof to the landlord?", send_detail: "The landlord will only see “yes” for each requirement. Your documents stay here.",
      yes_send: "Yes, send it", cancel: "Cancel",
      sent_wait: "Sent. It reaches the landlord in about 1–2 minutes.", sent_ok: "The landlord has received your proof.",
      t4_title: "Deposit", dep_q: "Pay the deposit of {amount}?", pay: "Pay {amount}", not_now: "Not now",
      dep_wait: "Payment sent. It arrives in about 1–2 minutes.", dep_ok: "Deposit paid. The flat is yours to confirm with the landlord. 🎉",
      waiting_landlord: "Waiting for the landlord to check your proof…",
      l1_title: "What kind of tenant are you looking for?", l1_text: "Write it in your own words. Your assistant fills in the form for you – you can change everything.",
      fill: "Fill in the form for me", filling: "Your assistant is reading…",
      l_rules: "Your requirements", rent: "Monthly rent", deposit: "Deposit", publish: "Publish my request",
      l2_title: "Your request is published", l2_wait: "Waiting for a tenant to send their proof…",
      l_arriving: "A tenant's proof is on its way (about 1–2 minutes)…", l_checking: "Checking the proof…",
      l_ok: "This tenant meets all your requirements", l_bad: "This proof was refused",
      l_never: "You did not see any document, salary, name or address.",
      l_dep_req: "Your assistant asked the tenant for the deposit of {amount}.", l_dep_ok: "Deposit of {amount} received ✓",
      new_request: "Change my request", tech: "Show technical details", helper: "Your assistant",
      reset: "Reset demo", dev: "Developer view", wallets: "Wallets",
      identity: "Is an adult (18 or older)",
      income: "Earns at least {x} per month",
      occ_student: "Is a student", occ_employed: "Has a job", occ_either: "Is a student or has a job", occ_until: "until {d}",
      savings: "Has at least {x} in savings", guarantor: "Has a guarantor who earns at least {x} per month",
      d_identity: "Identity certificate", s_identity: "from your municipality (comune)",
      d_income: "Income statement", s_income: "from your bank",
      d_occupation: "Enrolment certificate or work contract", s_occupation: "from your university or employer",
      d_savings: "Balance certificate", s_savings: "from your bank",
      d_guarantor: "Guarantor's income statement", s_guarantor: "from your guarantor's bank",
      home_title: "Who are you?", home_tenant: "I'm looking for a flat", home_landlord: "I'm renting out a flat",
      home_text: "Prove you qualify for a flat without showing your documents.",
    },
    it: {
      tenant: "Inquilino", landlord: "Proprietario", step: "Passo {a} di {b}",
      t_wait_title: "In attesa di un proprietario", t_wait_text: "Quando un proprietario pubblica le sue richieste, appaiono qui.",
      t1_title: "Il proprietario vorrebbe sapere", t1_next: "Continua",
      t2_title: "Aggiungi i tuoi documenti ufficiali", t2_text: "Sono accettati solo documenti firmati dalla banca, dal comune, dall'università o dal datore di lavoro. Restano su questo computer.",
      choose: "Scegli il file", use_demo: "Usa documento demo", try_fake: "Prova un documento modificato (demo)",
      missing: "Non ancora aggiunto", original: "Originale, firmato da {issuer}", refused: "Non accettato",
      t2_next: "Documenti aggiunti – continua",
      t3_title: "Crea la tua prova privata", t3_text: "Il tuo computer controlla i documenti con le regole del proprietario e crea una prova. La prova dice solo “sì” per ogni regola – niente nomi, importi o documenti.",
      make_proof: "Crea la mia prova privata", proving: "Un momento… circa 10 secondi",
      proof_ready: "La tua prova è pronta", proof_none: "Non è possibile creare la prova: almeno una regola non è soddisfatta.",
      send: "Invia al proprietario", send_q: "Inviare la prova al proprietario?", send_detail: "Il proprietario vedrà solo “sì” per ogni requisito. I tuoi documenti restano qui.",
      yes_send: "Sì, invia", cancel: "Annulla",
      sent_wait: "Inviata. Arriva al proprietario in circa 1–2 minuti.", sent_ok: "Il proprietario ha ricevuto la tua prova.",
      t4_title: "Deposito", dep_q: "Pagare il deposito di {amount}?", pay: "Paga {amount}", not_now: "Non ora",
      dep_wait: "Pagamento inviato. Arriva in circa 1–2 minuti.", dep_ok: "Deposito pagato. 🎉",
      waiting_landlord: "In attesa che il proprietario controlli la prova…",
      l1_title: "Che tipo di inquilino cerchi?", l1_text: "Scrivilo con parole tue. Il tuo assistente compila il modulo – puoi cambiare tutto.",
      fill: "Compila il modulo per me", filling: "Il tuo assistente sta leggendo…",
      l_rules: "I tuoi requisiti", rent: "Affitto mensile", deposit: "Deposito", publish: "Pubblica la richiesta",
      l2_title: "La tua richiesta è pubblicata", l2_wait: "In attesa che un inquilino invii la sua prova…",
      l_arriving: "La prova di un inquilino sta arrivando (circa 1–2 minuti)…", l_checking: "Controllo della prova…",
      l_ok: "Questo inquilino soddisfa tutti i requisiti", l_bad: "Questa prova è stata rifiutata",
      l_never: "Non hai visto documenti, stipendio, nome o indirizzo.",
      l_dep_req: "Il tuo assistente ha chiesto il deposito di {amount}.", l_dep_ok: "Deposito di {amount} ricevuto ✓",
      new_request: "Modifica la richiesta", tech: "Mostra dettagli tecnici", helper: "Il tuo assistente",
      reset: "Ricomincia demo", dev: "Vista sviluppatore", wallets: "Portafogli",
      identity: "È maggiorenne (18 anni o più)",
      income: "Guadagna almeno {x} al mese",
      occ_student: "È uno studente", occ_employed: "Ha un lavoro", occ_either: "È studente o ha un lavoro", occ_until: "fino al {d}",
      savings: "Ha almeno {x} di risparmi", guarantor: "Ha un garante che guadagna almeno {x} al mese",
      d_identity: "Certificato anagrafico", s_identity: "dal tuo comune",
      d_income: "Attestazione di reddito", s_income: "dalla tua banca",
      d_occupation: "Certificato di iscrizione o contratto di lavoro", s_occupation: "dall'università o dal datore di lavoro",
      d_savings: "Certificato di saldo", s_savings: "dalla tua banca",
      d_guarantor: "Reddito del garante", s_guarantor: "dalla banca del garante",
      home_title: "Chi sei?", home_tenant: "Cerco casa", home_landlord: "Affitto una casa",
      home_text: "Dimostra di avere i requisiti per una casa senza mostrare i tuoi documenti.",
    },
    tr: {
      tenant: "Kiracı", landlord: "Ev sahibi", step: "Adım {a} / {b}",
      t_wait_title: "Ev sahibi bekleniyor", t_wait_text: "Bir ev sahibi isteklerini yayınladığında burada görünür.",
      t1_title: "Ev sahibi şunları bilmek istiyor", t1_next: "Devam et",
      t2_title: "Resmi belgelerinizi ekleyin", t2_text: "Yalnızca bankanız, belediye, üniversiteniz veya işvereniniz tarafından imzalanmış belgeler kabul edilir. Belgeler bu bilgisayarda kalır.",
      choose: "Dosya seç", use_demo: "Demo belgeyi kullan", try_fake: "Değiştirilmiş bir belge dene (demo)",
      missing: "Henüz eklenmedi", original: "Orijinal, imzalayan: {issuer}", refused: "Kabul edilmedi",
      t2_next: "Belgeler eklendi – devam et",
      t3_title: "Gizli kanıtınızı oluşturun", t3_text: "Bilgisayarınız belgelerinizi ev sahibinin kurallarıyla karşılaştırır ve bir kanıt oluşturur. Kanıt her kural için yalnızca “evet” der – isim, tutar veya belge yok.",
      make_proof: "Gizli kanıtımı oluştur", proving: "Hazırlanıyor… yaklaşık 10 saniye",
      proof_ready: "Kanıtınız hazır", proof_none: "Kanıt oluşturulamıyor: en az bir kural karşılanmıyor.",
      send: "Ev sahibine gönder", send_q: "Kanıtınız ev sahibine gönderilsin mi?", send_detail: "Ev sahibi her şart için yalnızca “evet” görür. Belgeleriniz burada kalır.",
      yes_send: "Evet, gönder", cancel: "Vazgeç",
      sent_wait: "Gönderildi. Yaklaşık 1–2 dakikada ev sahibine ulaşır.", sent_ok: "Ev sahibi kanıtınızı aldı.",
      t4_title: "Depozito", dep_q: "{amount} depozito ödensin mi?", pay: "{amount} öde", not_now: "Şimdi değil",
      dep_wait: "Ödeme gönderildi. Yaklaşık 1–2 dakikada ulaşır.", dep_ok: "Depozito ödendi. 🎉",
      waiting_landlord: "Ev sahibinin kanıtı kontrol etmesi bekleniyor…",
      l1_title: "Nasıl bir kiracı arıyorsunuz?", l1_text: "Kendi cümlelerinizle yazın. Asistanınız formu doldurur – her şeyi değiştirebilirsiniz.",
      fill: "Formu benim için doldur", filling: "Asistanınız okuyor…",
      l_rules: "Şartlarınız", rent: "Aylık kira", deposit: "Depozito", publish: "İsteğimi yayınla",
      l2_title: "İsteğiniz yayınlandı", l2_wait: "Bir kiracının kanıtını göndermesi bekleniyor…",
      l_arriving: "Bir kiracının kanıtı geliyor (yaklaşık 1–2 dakika)…", l_checking: "Kanıt kontrol ediliyor…",
      l_ok: "Bu kiracı tüm şartlarınızı karşılıyor", l_bad: "Bu kanıt reddedildi",
      l_never: "Hiçbir belge, maaş, isim veya adres görmediniz.",
      l_dep_req: "Asistanınız kiracıdan {amount} depozito istedi.", l_dep_ok: "{amount} depozito alındı ✓",
      new_request: "İsteğimi değiştir", tech: "Teknik ayrıntıları göster", helper: "Asistanınız",
      reset: "Demoyu sıfırla", dev: "Geliştirici görünümü", wallets: "Cüzdanlar",
      identity: "Reşit (18 yaş veya üstü)",
      income: "Ayda en az {x} kazanıyor",
      occ_student: "Öğrenci", occ_employed: "Bir işi var", occ_either: "Öğrenci veya bir işi var", occ_until: "{d} tarihine kadar",
      savings: "En az {x} birikimi var", guarantor: "Ayda en az {x} kazanan bir kefili var",
      d_identity: "Nüfus/ikamet belgesi", s_identity: "belediyenizden",
      d_income: "Gelir belgesi", s_income: "bankanızdan",
      d_occupation: "Öğrenci belgesi veya iş sözleşmesi", s_occupation: "üniversitenizden veya işvereninizden",
      d_savings: "Bakiye belgesi", s_savings: "bankanızdan",
      d_guarantor: "Kefilin gelir belgesi", s_guarantor: "kefilin bankasından",
      home_title: "Siz kimsiniz?", home_tenant: "Ev arıyorum", home_landlord: "Evimi kiraya veriyorum",
      home_text: "Belgelerinizi göstermeden bir ev için şartları karşıladığınızı kanıtlayın.",
    },
  };
  S.t = (key, vars) => {
    let s = (T[lang] && T[lang][key]) || T.en[key] || key;
    for (const [k, v] of Object.entries(vars || {})) s = s.replace("{" + k + "}", v);
    return s;
  };

  S.SLOTS = ["identity", "income", "occupation", "savings", "guarantor"];
  S.SAMPLE = { identity: "1_identity.pdf", income: "2_income.pdf", occupation: "3_enrolment.pdf", savings: "4_savings.pdf", guarantor: "5_guarantor.pdf" };
  // A landlord rule in plain words
  S.ruleText = (slot, r) => {
    if (slot === "identity") return S.t("identity");
    if (slot === "income") return S.t("income", { x: amt(r.minIncome) });
    if (slot === "savings") return S.t("savings", { x: amt(r.minSavings) });
    if (slot === "guarantor") return S.t("guarantor", { x: amt(r.minGuarantor) });
    const base = r.allowStudent && r.allowEmployed ? S.t("occ_either") : r.allowStudent ? S.t("occ_student") : S.t("occ_employed");
    return r.leaseEnd ? base + " " + S.t("occ_until", { d: new Date(r.leaseEnd + "T00:00:00Z").toLocaleDateString(lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) }) : base;
  };
  S.ticked = (r) => S.SLOTS.filter((s) => r.checks[s]);

  // Assistant text from the local AI (with fixed fallback on the server). Cached per key.
  const cache = {};
  S.explain = async (kind, facts, key) => {
    const k = kind + "|" + S.lang() + "|" + (key || JSON.stringify(facts));
    if (!cache[k]) cache[k] = S.api("/api/ai/explain", { kind, lang: S.lang(), facts }).catch(() => ({ text: "", source: "error" }));
    return cache[k];
  };
  S.helperHtml = (text, source) => text ? `<div class="helper"><div class="who">💬 ${S.esc(S.t("helper"))}${source === "qvac" ? " · local AI" : ""}</div>${S.esc(text)}</div>` : "";

  S.langSelect = (onChange) => {
    const sel = document.createElement("select");
    sel.className = "lang"; sel.setAttribute("aria-label", "Language");
    sel.innerHTML = '<option value="en">English</option><option value="it">Italiano</option><option value="tr">Türkçe</option>';
    sel.value = lang;
    sel.onchange = () => { S.setLang(sel.value); onChange(); };
    return sel;
  };
  window.KP = S;
})();
