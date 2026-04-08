-- KisanMitra - Seed Data: 20 Popular Government Schemes
-- These are loaded on first database setup

INSERT INTO schemes (scheme_code, name_en, name_hi, ministry, department, scheme_type, state, sector, subsector, eligibility_criteria, benefit_type, subsidy_percentage, max_subsidy_amount, loan_amount_max, interest_subsidy, application_url, documents_required, application_process, description_en, description_hi, is_active)
VALUES

-- 1. PMFME
('PMFME', 'PM Formalization of Micro Food Processing Enterprises', 'प्रधानमंत्री सूक्ष्म खाद्य प्रसंस्करण उद्यम औपचारिकीकरण योजना',
 'Ministry of Food Processing Industries', 'MOFPI', 'central', NULL, 'food_processing', 'micro_food',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["farmer","msme_owner","shg_member"],"is_woman_priority":true,"is_sc_st_priority":true}',
 'subsidy', 35.00, 1000000, NULL, NULL, 'https://pmfme.mofpi.gov.in',
 '["Aadhaar Card","PAN Card","Bank Passbook","DPR","Quotations for Machinery"]',
 'Apply online through PMFME portal or through nearest District Resource Person',
 '35% credit-linked subsidy up to Rs.10 lakh for micro food processing units. Covers machinery, packaging, and working capital.',
 'सूक्ष्म खाद्य प्रसंस्करण इकाइयों के लिए 35% क्रेडिट-लिंक्ड सब्सिडी, अधिकतम 10 लाख रुपये।', true),

-- 2. MUDRA Shishu
('MUDRA_SHISHU', 'MUDRA Loan - Shishu', 'मुद्रा ऋण - शिशु',
 'Ministry of Finance', 'DFS', 'central', NULL, 'msme', 'micro_enterprise',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"age_max":65,"occupation":["any"],"udyam_required":false}',
 'loan', NULL, NULL, 50000, NULL, 'https://www.mudra.org.in',
 '["Aadhaar Card","PAN Card","2 Passport Photos","Business Plan"]',
 'Apply at any bank branch, NBFC, or MFI. No collateral required.',
 'Loans up to Rs.50,000 for small/micro enterprises under PMMY. No collateral or guarantor needed.',
 'पीएमएमवाई के तहत छोटे/सूक्ष्म उद्यमों के लिए 50,000 रुपये तक का ऋण। कोई जमानत नहीं।', true),

-- 3. MUDRA Kishor
('MUDRA_KISHOR', 'MUDRA Loan - Kishor', 'मुद्रा ऋण - किशोर',
 'Ministry of Finance', 'DFS', 'central', NULL, 'msme', 'small_enterprise',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"age_max":65,"occupation":["msme_owner"],"existing_business":true}',
 'loan', NULL, NULL, 500000, NULL, 'https://www.mudra.org.in',
 '["Aadhaar Card","PAN Card","Business Proof","Bank Statement 6 months","ITR"]',
 'Apply at any bank branch with business proof and financial statements.',
 'Loans from Rs.50,001 to Rs.5 lakh for existing small businesses under PMMY.',
 'पीएमएमवाई के तहत मौजूदा छोटे व्यवसायों के लिए 50,001 से 5 लाख रुपये तक का ऋण।', true),

-- 4. MUDRA Tarun
('MUDRA_TARUN', 'MUDRA Loan - Tarun', 'मुद्रा ऋण - तरुण',
 'Ministry of Finance', 'DFS', 'central', NULL, 'msme', 'medium_enterprise',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"age_max":65,"occupation":["msme_owner"],"existing_business":true}',
 'loan', NULL, NULL, 1000000, NULL, 'https://www.mudra.org.in',
 '["Aadhaar Card","PAN Card","Business Registration","Bank Statement 12 months","ITR 2 years","Project Report"]',
 'Apply at any bank branch with detailed business plan and financial records.',
 'Loans from Rs.5,00,001 to Rs.10 lakh for established businesses under PMMY.',
 'पीएमएमवाई के तहत स्थापित व्यवसायों के लिए 5 लाख से 10 लाख रुपये तक का ऋण।', true),

-- 5. KCC
('KCC', 'Kisan Credit Card', 'किसान क्रेडिट कार्ड',
 'Ministry of Agriculture', 'DAC&FW', 'central', NULL, 'agriculture', 'crop_loan',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"age_max":75,"occupation":["farmer"],"land_required":true}',
 'loan', NULL, NULL, 300000, 5.00, 'https://pmkisan.gov.in',
 '["Aadhaar Card","Land Records/Patta","Bank Passbook","2 Photos"]',
 'Apply at nearest bank branch with land ownership documents.',
 'Short-term crop loan up to Rs.3 lakh at 4% interest (with subvention). Includes crop insurance and personal accident cover.',
 'किसानों के लिए 4% ब्याज दर पर 3 लाख रुपये तक का अल्पकालिक फसल ऋण।', true),

-- 6. NABARD DEDS
('NABARD_DEDS', 'NABARD Dairy Entrepreneurship Development Scheme', 'नाबार्ड डेयरी उद्यमिता विकास योजना',
 'NABARD', 'Dairy Development', 'central', NULL, 'dairy', 'dairy_farm',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["farmer","msme_owner"],"is_sc_st_priority":true}',
 'subsidy', 25.00, 1000000, 1000000, NULL, 'https://www.nabard.org',
 '["Aadhaar Card","Land Records","Bank Passbook","DPR","Quotations"]',
 'Apply through any commercial bank or regional rural bank with DPR.',
 '25% subsidy (33.33% for SC/ST) for setting up dairy farms, milk processing units. Max 10 milch animals.',
 'डेयरी फार्म स्थापित करने के लिए 25% सब्सिडी (अनुसूचित जाति/जनजाति के लिए 33.33%)।', true),

-- 7. PMEGP
('PMEGP', 'PM Employment Generation Programme', 'प्रधानमंत्री रोजगार सृजन कार्यक्रम',
 'Ministry of MSME', 'KVIC', 'central', NULL, 'msme', 'new_enterprise',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"education_min":"8th_pass","occupation":["any"],"income_max":null}',
 'subsidy', 25.00, 2500000, 2500000, NULL, 'https://www.kviconline.gov.in/pmegpeportal',
 '["Aadhaar Card","Education Certificate","Caste Certificate","DPR","Bank Passbook"]',
 'Apply online on KVIC portal. 15-35% subsidy based on category and area.',
 '15-35% subsidy for setting up new micro enterprises. Max Rs.25 lakh (manufacturing) or Rs.10 lakh (service sector).',
 'नए सूक्ष्म उद्यमों की स्थापना के लिए 15-35% सब्सिडी। अधिकतम 25 लाख (विनिर्माण)।', true),

-- 8. NLM
('NLM', 'National Livestock Mission', 'राष्ट्रीय पशुधन मिशन',
 'Ministry of Fisheries, Animal Husbandry & Dairying', 'DAHD', 'central', NULL, 'livestock', 'livestock_development',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["farmer","msme_owner"]}',
 'subsidy', 50.00, 5000000, NULL, NULL, 'https://dahd.nic.in',
 '["Aadhaar Card","Land Records","Bank Passbook","DPR","Veterinary Certificate"]',
 'Apply through State Animal Husbandry Department or DAHD portal.',
 '50% subsidy for entrepreneurship in livestock sector including poultry, sheep, goat, pig farming and feed/fodder.',
 'पशुधन क्षेत्र में उद्यमिता के लिए 50% सब्सिडी - मुर्गीपालन, बकरी, भेड़, सुअर पालन।', true),

-- 9. AHIDF
('AHIDF', 'Animal Husbandry Infrastructure Development Fund', 'पशुपालन अवसंरचना विकास निधि',
 'Ministry of Fisheries, Animal Husbandry & Dairying', 'DAHD', 'central', NULL, 'livestock', 'infra',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["farmer","msme_owner","cooperative"]}',
 'interest_subsidy', NULL, NULL, 20000000, 3.00, 'https://ahidf.udyamimitra.in',
 '["Aadhaar Card","Business Registration","DPR","Bank Passbook","Land Documents"]',
 'Apply online through Udyami Mitra portal for animal husbandry infrastructure projects.',
 '3% interest subsidy on loans up to Rs.2 crore for dairy, meat processing, animal feed plants.',
 'डेयरी, मांस प्रसंस्करण, पशु आहार संयंत्रों के लिए 2 करोड़ तक के ऋण पर 3% ब्याज सब्सिडी।', true),

-- 10. PM Vishwakarma
('PM_VISHWAKARMA', 'PM Vishwakarma Yojana', 'प्रधानमंत्री विश्वकर्मा योजना',
 'Ministry of MSME', 'MSME', 'central', NULL, 'msme', 'artisan',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["artisan","craftsman"]}',
 'loan', NULL, NULL, 300000, 5.00, 'https://pmvishwakarma.gov.in',
 '["Aadhaar Card","Caste/Skill Certificate","Bank Passbook","2 Photos"]',
 'Apply through nearest CSC or pmvishwakarma.gov.in portal.',
 'Collateral-free loans up to Rs.3 lakh at 5% for 18 traditional trades. Includes skill training and toolkit.',
 '18 पारंपरिक व्यवसायों के लिए 5% ब्याज पर 3 लाख तक का ऋण। कौशल प्रशिक्षण और टूलकिट शामिल।', true),

-- 11. Stand-Up India
('STANDUP_INDIA', 'Stand-Up India', 'स्टैंड-अप इंडिया',
 'Ministry of Finance', 'DFS', 'central', NULL, 'msme', 'sc_st_women',
 '{"categories":["sc","st"],"gender":["male","female"],"age_min":18,"occupation":["any"],"is_woman_priority":true,"is_sc_st_priority":true}',
 'loan', NULL, NULL, 10000000, NULL, 'https://www.standupmitra.in',
 '["Aadhaar Card","Caste Certificate","Business Plan","Bank Statement","ITR"]',
 'Apply through Stand-Up Mitra portal or any scheduled bank branch.',
 'Loans from Rs.10 lakh to Rs.1 crore for SC/ST and women entrepreneurs for greenfield enterprises.',
 'अनुसूचित जाति/जनजाति और महिला उद्यमियों के लिए 10 लाख से 1 करोड़ तक का ऋण।', true),

-- 12. Startup India Seed Fund
('SISFS', 'Startup India Seed Fund Scheme', 'स्टार्टअप इंडिया सीड फंड योजना',
 'DPIIT', 'Startup India', 'central', NULL, 'startup', 'seed_fund',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"occupation":["startup"],"dpiit_recognized":true}',
 'grant', NULL, 5000000, NULL, NULL, 'https://seedfund.startupindia.gov.in',
 '["DPIIT Recognition Certificate","Business Plan","Incorporation Certificate","Bank Statement"]',
 'Apply through Startup India Seed Fund portal after DPIIT recognition.',
 'Up to Rs.50 lakh seed funding for DPIIT-recognized startups through approved incubators.',
 'डीपीआईआईटी मान्यता प्राप्त स्टार्टअप्स के लिए 50 लाख तक की सीड फंडिंग।', true),

-- 13. PM-KISAN
('PM_KISAN', 'PM Kisan Samman Nidhi', 'प्रधानमंत्री किसान सम्मान निधि',
 'Ministry of Agriculture', 'DAC&FW', 'central', NULL, 'agriculture', 'income_support',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"occupation":["farmer"],"land_required":true}',
 'dbt', NULL, 6000, NULL, NULL, 'https://pmkisan.gov.in',
 '["Aadhaar Card","Land Records","Bank Passbook"]',
 'Apply at nearest CSC or through state agriculture department.',
 'Rs.6,000 per year direct benefit transfer in 3 installments to all landholder farmer families.',
 'सभी भूमिधारक किसान परिवारों को 3 किस्तों में प्रति वर्ष 6,000 रुपये का सीधा लाभ हस्तांतरण।', true),

-- 14. PMFBY
('PMFBY', 'PM Fasal Bima Yojana', 'प्रधानमंत्री फसल बीमा योजना',
 'Ministry of Agriculture', 'DAC&FW', 'central', NULL, 'agriculture', 'crop_insurance',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"occupation":["farmer"]}',
 'subsidy', NULL, NULL, NULL, NULL, 'https://pmfby.gov.in',
 '["Aadhaar Card","Land Records","Bank Passbook","Sowing Certificate"]',
 'Apply through bank branch or CSC center before sowing season deadline.',
 'Crop insurance at 2% premium for Kharif, 1.5% for Rabi, 5% for commercial crops. Government pays remaining premium.',
 'खरीफ के लिए 2%, रबी के लिए 1.5% प्रीमियम पर फसल बीमा। शेष प्रीमियम सरकार देती है।', true),

-- 15. PM SVANidhi
('PM_SVANIDHI', 'PM Street Vendors AtmaNirbhar Nidhi', 'पीएम स्ट्रीट वेंडर्स आत्मनिर्भर निधि',
 'Ministry of Housing & Urban Affairs', 'MoHUA', 'central', NULL, 'financial_inclusion', 'street_vendor',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"age_min":18,"occupation":["street_vendor"]}',
 'loan', NULL, NULL, 50000, 7.00, 'https://pmsvanidhi.mohua.gov.in',
 '["Aadhaar Card","Vending Certificate/Letter of Recommendation","Bank Passbook","Photo"]',
 'Apply online or through nearest bank/ULB office.',
 'Working capital loan: Rs.10K (1st tranche), Rs.20K (2nd), Rs.50K (3rd). 7% interest subsidy on timely repayment.',
 'कार्यशील पूंजी ऋण: पहली किस्त 10 हजार, दूसरी 20 हजार, तीसरी 50 हजार। समय पर भुगतान पर 7% ब्याज सब्सिडी।', true),

-- 16. DAY-NRLM
('DAY_NRLM', 'Deendayal Antyodaya Yojana - NRLM', 'दीनदयाल अंत्योदय योजना - एनआरएलएम',
 'Ministry of Rural Development', 'MoRD', 'central', NULL, 'rural', 'livelihoods',
 '{"categories":["general","obc","sc","st"],"gender":["female"],"occupation":["any"],"is_woman_priority":true}',
 'grant', NULL, NULL, NULL, NULL, 'https://nrlm.gov.in',
 '["Aadhaar Card","BPL Card/Proof","Bank Passbook","SHG Membership"]',
 'Join nearest SHG through block-level NRLM staff.',
 'Self-help group formation, bank linkage, skill training, and revolving fund for rural women.',
 'ग्रामीण महिलाओं के लिए स्वयं सहायता समूह गठन, बैंक लिंकेज, कौशल प्रशिक्षण।', true),

-- 17. PMKSY
('PMKSY', 'PM Krishi Sinchayee Yojana', 'प्रधानमंत्री कृषि सिंचाई योजना',
 'Ministry of Agriculture', 'DAC&FW', 'central', NULL, 'agriculture', 'irrigation',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"occupation":["farmer"],"land_required":true}',
 'subsidy', 55.00, 500000, NULL, NULL, 'https://pmksy.gov.in',
 '["Aadhaar Card","Land Records","Bank Passbook","Quotation for Drip/Sprinkler"]',
 'Apply through state agriculture department or district agriculture officer.',
 '55% subsidy (general) and 70% (SC/ST/small farmers) on micro irrigation systems (drip, sprinkler).',
 'सूक्ष्म सिंचाई (ड्रिप, स्प्रिंकलर) पर 55% सब्सिडी (सामान्य) और 70% (SC/ST/लघु किसान)।', true),

-- 18. PM Ujjwala
('PM_UJJWALA', 'PM Ujjwala Yojana', 'प्रधानमंत्री उज्ज्वला योजना',
 'Ministry of Petroleum & Natural Gas', 'MoPNG', 'central', NULL, 'women', 'lpg',
 '{"categories":["general","obc","sc","st"],"gender":["female"],"income_max":200000,"occupation":["any"],"is_woman_priority":true}',
 'subsidy', 100.00, 1600, NULL, NULL, 'https://www.pmuy.gov.in',
 '["Aadhaar Card","BPL Card/Ration Card","Bank Passbook"]',
 'Apply at nearest LPG distributor with BPL documents.',
 'Free LPG connection (Rs.1,600 subsidy) to BPL households in the name of adult woman of the household.',
 'बीपीएल परिवारों की वयस्क महिला के नाम पर मुफ्त एलपीजी कनेक्शन।', true),

-- 19. Sukanya Samriddhi
('SUKANYA_SAMRIDDHI', 'Sukanya Samriddhi Yojana', 'सुकन्या समृद्धि योजना',
 'Ministry of Finance', 'DFS', 'central', NULL, 'women', 'savings',
 '{"categories":["general","obc","sc","st"],"gender":["female"],"age_max":10}',
 'interest_subsidy', NULL, NULL, NULL, 8.20, 'https://www.nsiindia.gov.in',
 '["Birth Certificate of Girl Child","Aadhaar of Parent","Address Proof","2 Photos"]',
 'Open account at any post office or authorized bank for girl child up to age 10.',
 'Savings scheme for girl child with 8.2% interest. Min Rs.250/year, max Rs.1.5 lakh/year. Matures at age 21.',
 'बालिकाओं के लिए 8.2% ब्याज पर बचत योजना। न्यूनतम 250 रुपये/वर्ष, अधिकतम 1.5 लाख/वर्ष।', true),

-- 20. RKVY
('RKVY', 'Rashtriya Krishi Vikas Yojana', 'राष्ट्रीय कृषि विकास योजना',
 'Ministry of Agriculture', 'DAC&FW', 'central', NULL, 'agriculture', 'agri_development',
 '{"categories":["general","obc","sc","st"],"gender":["male","female"],"occupation":["farmer","agri_entrepreneur"]}',
 'grant', NULL, 2500000, NULL, NULL, 'https://rkvy.nic.in',
 '["Aadhaar Card","Business Plan/DPR","Land Records","Bank Passbook"]',
 'Apply through RKVY-RAFTAAR portal for agri-entrepreneurship or through state agriculture department.',
 'Financial support for agriculture and allied sector projects. Up to Rs.25 lakh for agri-startups under RAFTAAR.',
 'कृषि और संबद्ध क्षेत्र परियोजनाओं के लिए वित्तीय सहायता। रफ्तार के तहत कृषि स्टार्टअप के लिए 25 लाख तक।', true)

ON CONFLICT (scheme_code) DO NOTHING;
