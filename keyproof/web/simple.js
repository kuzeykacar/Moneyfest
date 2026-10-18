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
      ai_reading: "Your local AI is reading this document on this computer…", ai_by: "Read on this device by {m}", ai_rules: "Read on this device (simple rules – local AI is off)",
      ai_extra: "Also added – not needed for this flat", ai_ok: "Local AI pre-check: everything the landlord asks for looks met.", ai_issue: "Local AI pre-check found something to look at before you continue.",
      ai_note: "This pre-check is only advice for you. The landlord never sees it – they rely only on the signed data and the zero-knowledge proof.",
      drop: "Drag your signed PDFs here", drop_or: "or", drop_choose: "Choose files", drop_hint: "Add them all at once – KeyProof sorts them for you. Files stay on this device.",
      use_sample: "Use sample", presenter: "Presenter mode",
      flat: "The flat", l_flat: "Your flat", f_address: "Address", f_kind: "Type", f_movein: "Move-in", f_landlord: "Landlord", f_rent: "Rent", f_deposit: "Deposit", per_month: "/month",
      kinds: "Room in shared flat|Studio|1-bedroom flat|2-bedroom flat|3-bedroom flat",
      receipt_dl: "Print or save receipt", r_flat: "Flat", r_code: "Application", r_checks: "Requirements met", r_appr_tx: "Approval on Bitcoin",
      r_title: "Rental application receipt", r_note: "This receipt shows only which requirements were met. No personal documents were shared. The attached proof can be checked by anyone with open-source tools.",
      hero1: "Rent a flat without handing over your documents.", hero2: "Tenants prove they meet your requirements from documents their bank, comune and university already signed. Landlords see only a yes for each requirement.",
      for_landlords: "For landlords", for_tenants: "For tenants", start_req: "Create a tenant check", start_req_text: "Describe your ideal tenant, publish, and share the link on your listing.",
      apply_text: "Got a link or code from a landlord? Enter it to apply.",
      how1: "Signed by the issuer", how1t: "Your bank, comune or university already signs your documents digitally.",
      how2: "Proved on your device", how2t: "A zero-knowledge proof shows you meet the rules. Your data never leaves your computer.",
      how3: "Settled on Bitcoin", how3t: "The approval and the deposit move as RGB assets on Bitcoin.",
      admin: "Admin",
      zk_title: "The proof", zk_text: "Anyone can check this proof independently – a bank, a notary or a lawyer – without trusting KeyProof. It contains no personal data.",
      zk_dl: "Download proof", zk_check: "Check again now", zk_ok: "Proof valid", zk_bad: "Proof NOT valid", zk_how: "Independent check (developers):",
      completed: "Completed",
      done_title: "All done", done_t_sub: "Your deposit has arrived. Thank you for using KeyProof.", done_l_sub: "The deposit has arrived. Thank you for using KeyProof.",
      receipt: "Receipt", r_amount: "Deposit", r_date: "Date", r_proof: "Approval token", r_tx: "Payment",
      private_kept: "What stayed private", pk_t: "Your name, salary, savings, address and documents never left your computer.", pk_l: "You received only a yes for each requirement – no documents, no personal details.",
      next_title: "What happens next", next_t: "The landlord will contact you to sign the rental contract and hand over the keys.", next_l: "Contact the tenant through the platform where you met to sign the contract and hand over the keys.",
      new_app: "Apply for another flat", new_req: "Create a new request", view_tx: "View on the Bitcoin explorer",
      problem: "Something went wrong",
      pay_low: "There is not enough money in your wallet for this deposit (you have {have}). Please add funds and try again.",
      share_title: "Share with tenants", share_text: "Send this link to people interested in your flat – for example in your Idealista listing or chat. They can also scan the QR code or type the code.",
      copy: "Copy link", copied: "Copied", code_label: "Application code", private_title: "Your private dashboard",
      private_text: "This page's address is your private key to see applications. Don't share it.", copy_private: "Copy my private link",
      not_owner: "This dashboard is private", not_owner_text: "Open it with your private link, or create a new request.", create_new: "Create a new request",
      enter_title: "Enter your application code", enter_text: "The landlord gave you a link or a code like 7F3K-92QD (for example on Idealista).", open: "Open", code_wrong: "No application found for this code. Please check it.",
      home_code: "Have a code from a landlord?",
      approved: "The landlord approved you",
      st_req: "Landlord’s request", st_docs: "Documents", st_proof: "Private proof", st_dep: "Deposit", sl_desc: "Describe your tenant", sl_pub: "Request published", sl_res: "Result",
      wallet_title: "In your wallet", wallet_text: "Coming next: banks, comuni and universities can send signed credentials straight to your wallet, so no PDF is needed.",
      wallet_use: "Use these credentials", wallet_none: "Nothing in your wallet yet.", wallet_arriving: "Credentials are on their way to your wallet (about 1–2 minutes)…",
      or_pdf: "Or add signed PDF documents:", issuer: "Issuer",
      i_title: "Send official credentials", i_text: "Banca Demo, Demo Comune di Torino and Demo Politecnico send Elena's signed credentials straight to her wallet, on Bitcoin. In the future, this replaces PDF documents.",
      i_send: "Send credentials to Elena's wallet", i_sending: "Sending…", i_sent: "Sent. They arrive in about 1–2 minutes.", i_done: "Delivered to Elena's wallet ✓",
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
      dep_wait: "Payment sent. It arrives in about 1–2 minutes.", dep_ok: "Deposit paid. The flat is yours to confirm with the landlord.",
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
      ai_reading: "La tua IA locale sta leggendo questo documento su questo computer…", ai_by: "Letto su questo dispositivo da {m}", ai_rules: "Letto su questo dispositivo (regole semplici – IA locale spenta)",
      ai_extra: "Aggiunti anche – non necessari per questo appartamento", ai_ok: "Controllo dell'IA locale: tutti i requisiti sembrano soddisfatti.", ai_issue: "Il controllo dell'IA locale ha trovato qualcosa da verificare prima di continuare.",
      ai_note: "Questo controllo è solo un consiglio per te. Il proprietario non lo vede: si basa solo sui dati firmati e sulla prova a conoscenza zero.",
      drop: "Trascina qui i tuoi PDF firmati", drop_or: "oppure", drop_choose: "Scegli i file", drop_hint: "Aggiungili tutti insieme: KeyProof li ordina per te. I file restano su questo dispositivo.",
      use_sample: "Usa esempio", flat: "L'appartamento", l_flat: "Il tuo appartamento", f_address: "Indirizzo", f_kind: "Tipo", f_movein: "Ingresso", f_landlord: "Proprietario", f_rent: "Affitto", f_deposit: "Deposito", per_month: "/mese",
      kinds: "Stanza in appartamento condiviso|Monolocale|Bilocale|Trilocale|Quadrilocale",
      receipt_dl: "Stampa o salva la ricevuta", r_flat: "Appartamento", r_code: "Candidatura", r_checks: "Requisiti soddisfatti", r_appr_tx: "Approvazione su Bitcoin",
      r_title: "Ricevuta della candidatura", r_note: "Questa ricevuta mostra solo quali requisiti sono soddisfatti. Nessun documento personale è stato condiviso. La prova allegata può essere verificata da chiunque con strumenti open source.",
      hero1: "Affitta casa senza consegnare i tuoi documenti.", hero2: "Gli inquilini dimostrano di avere i requisiti con documenti già firmati da banca, comune e università. Il proprietario vede solo un sì per ogni requisito.",
      for_landlords: "Per i proprietari", for_tenants: "Per gli inquilini", start_req: "Crea una verifica inquilino", start_req_text: "Descrivi l'inquilino ideale, pubblica e condividi il link nel tuo annuncio.",
      apply_text: "Hai un link o un codice da un proprietario? Inseriscilo per candidarti.",
      how1: "Firmato dall'ente", how1t: "Banca, comune o università firmano già digitalmente i tuoi documenti.",
      how2: "Dimostrato sul tuo dispositivo", how2t: "Una prova a conoscenza zero mostra che rispetti le regole. I tuoi dati non lasciano il computer.",
      how3: "Regolato su Bitcoin", how3t: "L'approvazione e il deposito si muovono come asset RGB su Bitcoin.",
      zk_title: "La prova", zk_text: "Chiunque può verificare questa prova in modo indipendente – una banca, un notaio o un avvocato – senza fidarsi di KeyProof. Non contiene dati personali.",
      zk_dl: "Scarica la prova", zk_check: "Verifica di nuovo", zk_ok: "Prova valida", zk_bad: "Prova NON valida", zk_how: "Verifica indipendente (sviluppatori):",
      completed: "Completato",
      done_title: "Tutto fatto", done_t_sub: "Il tuo deposito è arrivato. Grazie per aver usato KeyProof.", done_l_sub: "Il deposito è arrivato. Grazie per aver usato KeyProof.",
      receipt: "Ricevuta", r_amount: "Deposito", r_date: "Data", r_proof: "Token di approvazione", r_tx: "Pagamento",
      private_kept: "Cosa è rimasto privato", pk_t: "Nome, stipendio, risparmi, indirizzo e documenti non hanno mai lasciato il tuo computer.", pk_l: "Hai ricevuto solo un sì per ogni requisito – nessun documento, nessun dato personale.",
      next_title: "Cosa succede ora", next_t: "Il proprietario ti contatterà per firmare il contratto e consegnare le chiavi.", next_l: "Contatta l'inquilino tramite la piattaforma dove vi siete trovati per firmare il contratto e consegnare le chiavi.",
      new_app: "Candidati per un'altra casa", new_req: "Crea una nuova richiesta", view_tx: "Vedi sull'explorer Bitcoin",
      problem: "Qualcosa è andato storto",
      pay_low: "Non ci sono abbastanza fondi nel portafoglio per questo deposito (hai {have}). Aggiungi fondi e riprova.",
      share_title: "Condividi con gli inquilini", share_text: "Invia questo link alle persone interessate – ad esempio nell'annuncio o nella chat di Idealista. Possono anche scansionare il QR o digitare il codice.",
      copy: "Copia link", copied: "Copiato", code_label: "Codice di candidatura", private_title: "La tua pagina privata",
      private_text: "L'indirizzo di questa pagina è la tua chiave privata per vedere le candidature. Non condividerlo.", copy_private: "Copia il mio link privato",
      not_owner: "Questa pagina è privata", not_owner_text: "Aprila con il tuo link privato o crea una nuova richiesta.", create_new: "Crea una nuova richiesta",
      enter_title: "Inserisci il codice di candidatura", enter_text: "Il proprietario ti ha dato un link o un codice come 7F3K-92QD (ad esempio su Idealista).", open: "Apri", code_wrong: "Nessuna candidatura trovata per questo codice. Controllalo.",
      home_code: "Hai un codice da un proprietario?",
      approved: "Il proprietario ti ha approvato",
      st_req: "Richiesta", st_docs: "Documenti", st_proof: "Prova privata", st_dep: "Deposito", sl_desc: "Descrivi l’inquilino", sl_pub: "Richiesta pubblicata", sl_res: "Risultato",
      wallet_title: "Nel tuo portafoglio", wallet_text: "Credenziali ufficiali inviate dalla banca, dal comune e dall'università direttamente al tuo portafoglio. Nessun PDF.",
      wallet_use: "Usa queste credenziali", wallet_none: "Ancora niente nel portafoglio.", wallet_arriving: "Le credenziali stanno arrivando (circa 1–2 minuti)…",
      or_pdf: "Oppure aggiungi documenti PDF firmati:", issuer: "Ente",
      i_title: "Invia credenziali ufficiali", i_text: "Banca Demo, Demo Comune di Torino e Demo Politecnico inviano le credenziali firmate di Elena direttamente al suo portafoglio, su Bitcoin. In futuro sostituiscono i PDF.",
      i_send: "Invia le credenziali a Elena", i_sending: "Invio…", i_sent: "Inviate. Arrivano in circa 1–2 minuti.", i_done: "Consegnate nel portafoglio di Elena ✓",
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
      dep_wait: "Pagamento inviato. Arriva in circa 1–2 minuti.", dep_ok: "Deposito pagato.",
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
      ai_reading: "Yerel yapay zekânız bu belgeyi bu bilgisayarda okuyor…", ai_by: "Bu cihazda {m} tarafından okundu", ai_rules: "Bu cihazda okundu (basit kurallar – yerel yapay zekâ kapalı)",
      ai_extra: "Ayrıca eklendi – bu daire için gerekmiyor", ai_ok: "Yerel yapay zekâ ön kontrolü: ev sahibinin istediği her şey karşılanıyor görünüyor.", ai_issue: "Yerel yapay zekâ ön kontrolü devam etmeden önce bakmanız gereken bir şey buldu.",
      ai_note: "Bu ön kontrol yalnızca sizin için bir tavsiyedir. Ev sahibi bunu görmez; yalnızca imzalı verilere ve sıfır bilgi kanıtına güvenir.",
      drop: "İmzalı PDF'lerinizi buraya sürükleyin", drop_or: "veya", drop_choose: "Dosya seçin", drop_hint: "Hepsini birden ekleyin, KeyProof sıralar. Dosyalar bu cihazda kalır.",
      use_sample: "Örneği kullan", flat: "Daire", l_flat: "Daireniz", f_address: "Adres", f_kind: "Tür", f_movein: "Taşınma", f_landlord: "Ev sahibi", f_rent: "Kira", f_deposit: "Depozito", per_month: "/ay",
      kinds: "Paylaşımlı evde oda|Stüdyo|1+1|2+1|3+1",
      receipt_dl: "Makbuzu yazdır veya kaydet", r_flat: "Daire", r_code: "Başvuru", r_checks: "Karşılanan şartlar", r_appr_tx: "Bitcoin'de onay",
      r_title: "Kira başvurusu makbuzu", r_note: "Bu makbuz yalnızca hangi şartların karşılandığını gösterir. Hiçbir kişisel belge paylaşılmadı. Ekteki kanıtı herkes açık kaynak araçlarla doğrulayabilir.",
      hero1: "Belgelerinizi teslim etmeden ev kiralayın.", hero2: "Kiracılar, bankanın, belediyenin ve üniversitenin zaten imzaladığı belgelerle şartları karşıladığını kanıtlar. Ev sahibi her şart için yalnızca bir evet görür.",
      for_landlords: "Ev sahipleri için", for_tenants: "Kiracılar için", start_req: "Kiracı kontrolü oluştur", start_req_text: "İdeal kiracınızı tarif edin, yayınlayın ve bağlantıyı ilanınızda paylaşın.",
      apply_text: "Ev sahibinden bağlantı veya kod mu aldınız? Başvurmak için girin.",
      how1: "Kurum tarafından imzalı", how1t: "Bankanız, belediyeniz veya üniversiteniz belgelerinizi zaten dijital olarak imzalıyor.",
      how2: "Cihazınızda kanıtlanır", how2t: "Sıfır bilgi kanıtı kurallara uyduğunuzu gösterir. Verileriniz bilgisayarınızdan çıkmaz.",
      how3: "Bitcoin'de tamamlanır", how3t: "Onay ve depozito Bitcoin üzerinde RGB varlığı olarak taşınır.",
      zk_title: "Kanıt", zk_text: "Bu kanıtı herkes bağımsız olarak doğrulayabilir – bir banka, noter veya avukat – KeyProof'a güvenmeden. Kişisel veri içermez.",
      zk_dl: "Kanıtı indir", zk_check: "Şimdi tekrar doğrula", zk_ok: "Kanıt geçerli", zk_bad: "Kanıt GEÇERSİZ", zk_how: "Bağımsız doğrulama (geliştiriciler):",
      completed: "Tamamlandı",
      done_title: "Her şey tamam", done_t_sub: "Depozitonuz ulaştı. KeyProof'u kullandığınız için teşekkürler.", done_l_sub: "Depozito ulaştı. KeyProof'u kullandığınız için teşekkürler.",
      receipt: "Makbuz", r_amount: "Depozito", r_date: "Tarih", r_proof: "Onay belirteci", r_tx: "Ödeme",
      private_kept: "Gizli kalanlar", pk_t: "Adınız, maaşınız, birikimleriniz, adresiniz ve belgeleriniz bilgisayarınızdan hiç çıkmadı.", pk_l: "Her şart için yalnızca bir evet aldınız – belge yok, kişisel bilgi yok.",
      next_title: "Sırada ne var", next_t: "Ev sahibi kira sözleşmesini imzalamak ve anahtarları teslim etmek için sizinle iletişime geçecek.", next_l: "Sözleşmeyi imzalamak ve anahtarları teslim etmek için kiracıyla tanıştığınız platform üzerinden iletişime geçin.",
      new_app: "Başka bir daireye başvur", new_req: "Yeni istek oluştur", view_tx: "Bitcoin gezgininde gör",
      problem: "Bir sorun oluştu",
      pay_low: "Cüzdanınızda bu depozito için yeterli para yok (mevcut: {have}). Lütfen bakiye ekleyip tekrar deneyin.",
      share_title: "Kiracılarla paylaşın", share_text: "Bu bağlantıyı dairenizle ilgilenenlere gönderin – örneğin Idealista ilanınızda veya sohbetinde. QR kodu tarayabilir ya da kodu yazabilirler.",
      copy: "Bağlantıyı kopyala", copied: "Kopyalandı", code_label: "Başvuru kodu", private_title: "Özel sayfanız",
      private_text: "Bu sayfanın adresi başvuruları görmeniz için özel anahtarınızdır. Paylaşmayın.", copy_private: "Özel bağlantımı kopyala",
      not_owner: "Bu sayfa özeldir", not_owner_text: "Özel bağlantınızla açın veya yeni bir istek oluşturun.", create_new: "Yeni istek oluştur",
      enter_title: "Başvuru kodunuzu girin", enter_text: "Ev sahibi size bir bağlantı veya 7F3K-92QD gibi bir kod verdi (örneğin Idealista'da).", open: "Aç", code_wrong: "Bu kodla bir başvuru bulunamadı. Lütfen kontrol edin.",
      home_code: "Ev sahibinden bir kodunuz mu var?",
      approved: "Ev sahibi sizi onayladı",
      st_req: "Ev sahibinin isteği", st_docs: "Belgeler", st_proof: "Gizli kanıt", st_dep: "Depozito", sl_desc: "Kiracıyı tanımlayın", sl_pub: "İstek yayınlandı", sl_res: "Sonuç",
      wallet_title: "Cüzdanınızda", wallet_text: "Bankanızın, belediyenin ve üniversitenizin doğrudan cüzdanınıza gönderdiği resmi belgeler. PDF gerekmez.",
      wallet_use: "Bu belgeleri kullan", wallet_none: "Cüzdanınızda henüz bir şey yok.", wallet_arriving: "Belgeler cüzdanınıza geliyor (yaklaşık 1–2 dakika)…",
      or_pdf: "Ya da imzalı PDF belgeleri ekleyin:", issuer: "Kurum",
      i_title: "Resmi belgeleri gönder", i_text: "Banca Demo, Demo Torino Belediyesi ve Demo Politeknik, Elena'nın imzalı belgelerini Bitcoin üzerinden doğrudan cüzdanına gönderir. Gelecekte PDF'lerin yerini alır.",
      i_send: "Belgeleri Elena'nın cüzdanına gönder", i_sending: "Gönderiliyor…", i_sent: "Gönderildi. Yaklaşık 1–2 dakikada ulaşır.", i_done: "Elena'nın cüzdanına ulaştı ✓",
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
      dep_wait: "Ödeme gönderildi. Yaklaşık 1–2 dakikada ulaşır.", dep_ok: "Depozito ödendi.",
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

  // Line icons (Lucide-style, ISC licence): simple and consistent, no emojis.
  const P = {
    key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a7 7 0 0 1 14 0v1"/>',
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    landmark: '<path d="M3 21h18"/><path d="M5 21V10"/><path d="M19 21V10"/><path d="M9.5 21V10"/><path d="M14.5 21V10"/><path d="m2 10 10-6 10 6"/>',
    bank: '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M7 15h3"/>',
    cap: '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
    file: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M14 3v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5"/><path d="M12 16.5v.01"/>',
    sparkle: '<path d="M12 3l1.8 4.9L19 9.7l-5.2 1.8L12 16.5l-1.8-5L5 9.7l5.2-1.8Z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8Z"/>',
    inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6Z"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    dot: '<circle cx="12" cy="12" r="3"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  };
  S.icon = (name, size) => `<svg class="ic" width="${size || 20}" height="${size || 20}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || P.dot}</svg>`;
  S.logo = () => document.querySelectorAll(".logo").forEach((el) => (el.innerHTML = `<span class="mark">${S.icon("key", 17)}</span><span>KeyProof</span>`));
  S.badge = (id, icon, text) => { const el = document.getElementById(id); if (el) el.innerHTML = S.icon(icon, 15) + "<span>" + S.esc(text) + "</span>"; };
  // Vertical step list in the side column (a compact bar on phones)
  S.steps = (labels, current) => {
    const ol = document.getElementById("progress");
    if (ol) ol.innerHTML = labels.map((l, i) => `<li class="${i + 1 < current ? "done" : i + 1 === current ? "on" : ""}"><span class="n">${i + 1 < current ? S.icon("check", 14) : i + 1}</span><span class="l">${S.esc(l)}</span></li>`).join("");
    const info = document.getElementById("stepinfo");
    if (info) info.innerHTML = current > labels.length ? S.esc(S.t("completed")) : current ? S.esc(S.t("step", { a: current, b: labels.length })) + `<span class="stepname"> · ${S.esc(labels[current - 1])}</span>` : "";
  };

  S.SLOTS = ["identity", "income", "occupation", "savings", "guarantor"];
  S.SAMPLE = { identity: "Certificato_anagrafico_Elena_Rossi.pdf", income: "Income_statement_Elena_Rossi.pdf", occupation: "Certificato_iscrizione_Elena_Rossi.pdf", savings: "Balance_certificate_Elena_Rossi.pdf", guarantor: "Guarantor_income_Marco_Rossi.pdf" };
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
  S.helperHtml = (text, source) => text ? `<div class="helper"><div class="who">${S.icon("sparkle", 14)} ${S.esc(S.t("helper"))}${source === "qvac" ? " · local AI" : ""}</div>${S.esc(text)}</div>` : "";

  S.langSelect = (onChange) => {
    const sel = document.createElement("select");
    sel.className = "lang"; sel.setAttribute("aria-label", "Language");
    sel.innerHTML = '<option value="en">English</option><option value="it">Italiano</option><option value="tr">Türkçe</option>';
    sel.value = lang;
    sel.onchange = () => { S.setLang(sel.value); onChange(); };
    return sel;
  };
  S.param = (k) => new URLSearchParams(location.search).get(k) || "";
  S.normCode = (c) => { c = String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, ""); return c.length === 8 ? c.slice(0, 4) + "-" + c.slice(4) : c; };
  S.copyText = async (text, btn) => {
    try { await navigator.clipboard.writeText(text); } catch (e) {
      const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (e2) { /* ignore */ } ta.remove();
    }
    if (btn) { const old = btn.innerHTML; btn.innerHTML = S.icon("check", 16) + " " + S.t("copied"); setTimeout(() => (btn.innerHTML = old), 1500); }
  };
  S.qrSvg = (text) => { try { const q = qrcode(0, "M"); q.addData(text); q.make(); return q.createSvgTag(6, 2); } catch (e) { return ""; } };
  // In-app dialogs (never the browser's white pop-ups)
  function dialog(title, text, okLabel, cancelLabel, danger) {
    return new Promise((resolve) => {
      const m = document.createElement("div");
      m.className = "modal"; m.style.display = "grid"; m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true");
      m.innerHTML = `<div class="box"><h2 class="withicon">${S.icon(danger ? "alert" : "dot", 22)} ${S.esc(title)}</h2>
        ${text ? `<p class="dim">${S.esc(text)}</p>` : ""}
        <div class="row" style="margin-top:18px"><button class="btn ${danger ? "" : "ok"}" data-a="ok">${S.esc(okLabel)}</button>
        ${cancelLabel ? `<button class="btn secondary" data-a="no">${S.esc(cancelLabel)}</button>` : ""}</div></div>`;
      const done = (v) => { m.remove(); document.removeEventListener("keydown", key); resolve(v); };
      const key = (e) => { if (e.key === "Escape") done(false); };
      m.addEventListener("click", (e) => { const a = e.target.closest("[data-a]"); if (a) done(a.dataset.a === "ok"); else if (e.target === m) done(false); });
      document.addEventListener("keydown", key);
      document.body.appendChild(m); m.querySelector("[data-a=ok]").focus();
    });
  }
  S.alert = (text, title) => dialog(title || S.t("problem"), text, "OK", null, true);
  S.confirm = (title, text, okLabel) => dialog(title, text, okLabel || "OK", S.t("cancel"), false);
  // Completion screen shared by tenant and landlord
  S.doneHtml = ({ sub, amount, token, txLink, privateText, nextText, items, againLabel }) => `
    <div class="card done"><div class="doneMark">${S.icon("check", 40)}</div>
      <h1>${S.esc(S.t("done_title"))}</h1><p class="dim lead">${S.esc(sub)}</p>
      ${items && items.length ? `<div class="doneChecks">${items.map((x) => `<div class="result-line"><span class="icon ok">${S.icon("check")}</span>${S.esc(x)}</div>`).join("")}</div>` : ""}
    </div>
    <div class="doneGrid">
      <div class="card"><h2 class="withicon">${S.icon("file")} ${S.esc(S.t("receipt"))}</h2>
        <dl class="receipt"><dt>${S.esc(S.t("r_amount"))}</dt><dd>${S.esc(amount)}</dd>
        <dt>${S.esc(S.t("r_date"))}</dt><dd>${new Date().toLocaleString(S.lang(), { dateStyle: "long", timeStyle: "short" })}</dd>
        ${token ? `<dt>${S.esc(S.t("r_proof"))}</dt><dd class="mono">${S.esc(token.slice(0, 24))}…</dd>` : ""}
        ${txLink ? `<dt>${S.esc(S.t("r_tx"))}</dt><dd><a href="${txLink}" target="_blank" rel="noopener">${S.esc(S.t("view_tx"))} ↗</a></dd>` : ""}</dl></div>
      <div class="card"><h2 class="withicon">${S.icon("lock")} ${S.esc(S.t("private_kept"))}</h2><p class="dim">${S.esc(privateText)}</p>
        <h2 class="withicon" style="margin-top:18px">${S.icon("home")} ${S.esc(S.t("next_title"))}</h2><p class="dim">${S.esc(nextText)}</p>
        <div class="row" style="margin-top:8px"><a class="btn" href="/receipt.html" target="_blank" rel="noopener">${S.icon("file", 18)} ${S.esc(S.t("receipt_dl"))}</a>
        <button class="btn secondary" id="again">${S.esc(againLabel)}</button></div></div>
    </div>
    <div class="card"><h2 class="withicon">${S.icon("shield")} ${S.esc(S.t("zk_title"))}</h2><p class="dim">${S.esc(S.t("zk_text"))}</p>
      <div class="row"><button class="btn" id="zkDl">${S.icon("file", 18)} ${S.esc(S.t("zk_dl"))}</button>
        <button class="btn secondary" id="zkCheck">${S.icon("shield", 18)} ${S.esc(S.t("zk_check"))}</button><span id="zkRes"></span></div>
      <p class="small dim" style="margin-top:14px">${S.esc(S.t("zk_how"))}</p>
      <div class="content mono small zkcmd">snarkjs groth16 verify verification_key.json public.json proof.json</div></div>`;
  // Buttons of the proof section (call after rendering the completion screen)
  S.bindProof = () => {
    const dl = document.getElementById("zkDl"), ck = document.getElementById("zkCheck");
    if (dl) dl.onclick = async () => {
      const b = await S.api("/api/proof");
      const vk = await (await fetch("zk/verification_key.json")).json();
      const file = { about: "KeyProof zero-knowledge proof (Groth16, BN254). Contains no personal data.",
        how_to_verify: "Save 'proof' as proof.json, 'publicSignals' as public.json, 'verification_key' as verification_key.json, then run: snarkjs groth16 verify verification_key.json public.json proof.json",
        public_signals_order: "holderTag, enabled[5], issuerAx[5], issuerAy[5], adultCutoff, minIncome, allowStudent, allowEmployed, leaseEnd, minSavings, minGuarantor, today, maxAgeDays, requestId",
        ...b, verification_key: vk };
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(file, null, 2)], { type: "application/json" }));
      a.download = "keyproof-proof-" + (b.code || "request") + ".json"; document.body.appendChild(a); a.click(); a.remove();
    };
    if (ck) ck.onclick = async () => {
      const res = document.getElementById("zkRes"); res.innerHTML = '<span class="spinner"></span>';
      try {
        const b = await S.api("/api/proof");
        const vk = await (await fetch("zk/verification_key.json")).json();
        const ok = await snarkjs.groth16.verify(vk, b.publicSignals, b.proof);
        res.innerHTML = `<span class="${ok ? "okText" : "badText"}">${S.icon(ok ? "check" : "x", 18)} ${S.esc(S.t(ok ? "zk_ok" : "zk_bad"))}</span>`;
      } catch (e) { res.innerHTML = `<span class="badText">${S.esc(e.message)}</span>`; }
    };
  };
  // What the local AI read from a document, and the private pre-check (tenant only)
  S.aiDocHtml = (d) => {
    const a = d && d.ai; if (!a) return "";
    if (a.status !== "done") return `<div class="aiRead"><span class="spinner"></span> ${S.esc(S.t("ai_reading"))}</div>`;
    const who = a.source === "qvac" ? S.t("ai_by", { m: "QVAC · " + (a.model || "local model") }) : S.t("ai_rules");
    const pc = d.precheck;
    const facts = [a.title, a.issuer && a.issuer !== a.title ? a.issuer : "", a.name].filter(Boolean).map(S.esc).join(" · ");
    return `<div class="aiRead"><div class="aiWho">${S.icon("sparkle", 14)} ${S.esc(who)}${a.seconds ? ` · ${a.seconds} s` : ""}</div>
      ${facts ? `<div class="aiFacts">${facts}</div>` : ""}
      ${pc ? pc.notes.map((n) => `<div class="aiNote ${n.ok ? "ok" : "bad"}">${S.icon(n.ok ? "check" : "alert", 15)} ${S.esc(n.text)}</div>`).join("") : ""}</div>`;
  };
  // Presenter mode (set on the admin page, this browser only): shows sample-document shortcuts
  S.presenter = () => { try { return localStorage.getItem("kp-presenter") === "1"; } catch (e) { return false; } };
  S.kindName = (i) => (S.t("kinds").split("|")[+i] || "");
  // The flat a request is for (address, type, move-in, rent, deposit)
  S.listingHtml = (req, title) => {
    const L = req.listing || {};
    const date = L.move_in ? new Date(L.move_in + "T00:00:00Z").toLocaleDateString(lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) : "";
    return `<div class="listing"><div class="lIcon">${S.icon("home", 26)}</div><div class="lBody">
      <div class="small dim">${S.esc(title || S.t("flat"))}</div>
      <div class="lTitle">${S.esc(L.address || "—")}</div>
      <div class="lMeta">${[L.kind !== undefined && L.kind !== "" ? S.esc(S.kindName(L.kind)) : "", date ? S.esc(S.t("f_movein")) + " " + S.esc(date) : "", L.landlord ? S.esc(S.t("f_landlord")) + ": " + S.esc(L.landlord) : ""].filter(Boolean).join(" · ")}</div></div>
      <div class="lPrice"><div class="lRent">${S.eur(req.rent)}<span class="dim small">${S.esc(S.t("per_month"))}</span></div>
      <div class="small dim">${S.esc(S.t("f_deposit"))} ${S.eur(req.deposit)}</div></div></div>`;
  };
  window.KP = S;
})();
