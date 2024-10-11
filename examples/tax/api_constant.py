from drf_yasg import openapi

valid_state_code = ['35', '37', '12', '18', '10', '04', '22', '26', '25', '07', '30',
                    '24', '06', '02', '01', '20', '29', '32', '31', '23', '27', '14',
                    '17', '15', '13', '21', '34', '03', '08', '11', '33', '36', '16',
                    '09', '05', '19', '38', '96', '97', '99', '100', '28']

valid_uqc_code = ['bag', 'bal', 'bdl', 'bgs', 'bkl', 'bnd', 'bou', 'box', 'btl', 'bun',
                  'can', 'cbm', 'ccm', 'cms', 'cmt', 'ctn', 'doz', 'drm', 'dzn', 'ggk',
                  'gms', 'grs', 'gyd', 'kgs', 'klr', 'kme', 'kms', 'ltr', 'mls', 'mlt',
                  'mtr', 'mts', 'nos', 'oth', 'pac', 'par', 'pcs', 'prs', 'qtl', 'qts',
                  'rol', 'set', 'sft', 'smt', 'sno', 'sqf', 'sqm', 'sqy', 'tbs', 'tgm',
                  'thd', 'ton', 'tub', 'ugs', 'unt', 'yds', 'oth', 'na']
valid_port_code = ['inabg1', 'inach1', 'inada6', 'inadi1', 'inagi1', 'inagr4', 'inagr5', 'inagr6', 'inagtb', 'inagx4',
                   'inahd6', 'inaig6', 'inaii6', 'inaik6', 'inair6', 'inaje6', 'inajj6', 'inajl4', 'inajm6', 'inakb6',
                   'inakd4', 'inakp6', 'inakr6', 'inakv6', 'inala1', 'inalf1', 'inamd4', 'inamd5', 'inamd6', 'inamg6',
                   'inami1', 'inamk6', 'inang1', 'inanl1', 'inapi6', 'inapl6', 'inapt6', 'inarr6', 'inasr2', 'inasr6',
                   'inatq4', 'inatq6', 'inatrb', 'inatt2', 'inawm6', 'inaws6', 'inaww6', 'inazk1', 'inbag6', 'inbai6',
                   'inbam6', 'inbap6', 'inbat6', 'inbau6', 'inbaw6', 'inbbi4', 'inbbm6', 'inbbp1', 'inbbs6', 'inbch6',
                   'inbco6', 'inbcp6', 'inbdb6', 'inbdg1', 'inbdh6', 'inbdi6', 'inbdm6', 'inbdq1', 'inbdr1', 'inbed1',
                   'inbek4', 'inbep4', 'inbet1', 'inbey1', 'inbfr6', 'inbgk6', 'inbgmb', 'inbgq6', 'inbgub', 'inbgw1',
                   'inbhc6', 'inbhd6', 'inbhj4', 'inbhl6', 'inbhm1', 'inbho4', 'inbhs6', 'inbhu1', 'inbhu4', 'inbkb4',
                   'inbkr1', 'inbkt1', 'inblc6', 'inble6', 'inblj6', 'inblk1', 'inblm1', 'inblp1', 'inblr4', 'inblr5',
                   'inblr6', 'inbltb', 'inblv6', 'inbma6', 'inbmr2', 'inbnc6', 'inbnd1', 'inbng6', 'inbnk6', 'inbnp1',
                   'inbnrb', 'inbnt6', 'inbnw6', 'inbnx6', 'inbnyb', 'inbok6', 'inbolb', 'inbom1', 'inbom4', 'inbom5',
                   'inbom6', 'inbpl5', 'inbps5', 'inbrab', 'inbrc6', 'inbrh1', 'inbri6', 'inbrl6', 'inbrm1', 'inbrs6',
                   'inbry1', 'inbsab', 'inbsb6', 'inbsl6', 'inbsn1', 'inbsr1', 'inbsw6', 'inbtk1', 'inbtmb', 'inbtr1',
                   'inbud1', 'inbul6', 'inbup4', 'inbup6', 'inbvc6', 'inbwd6', 'inbwn1', 'inbxr6', 'inbyt1', 'incag6',
                   'incam1', 'incap1', 'incar1', 'incas6', 'incbc6', 'incbd4', 'incbdb', 'incbe6', 'incbl1', 'incbs6',
                   'incch6', 'incci6', 'inccj1', 'inccj4', 'inccp6', 'inccq6', 'incct6', 'inccu1', 'inccu4', 'inccu5',
                   'inccw6', 'incdc6', 'incdd6', 'incdl1', 'incdp1', 'incdp4', 'incdp6', 'incdq6', 'incdr6', 'incec6',
                   'incga6', 'incge6', 'incgi6', 'incgl6', 'inche6', 'inchj6', 'inchl1', 'inchmb', 'inchn6', 'inchpb',
                   'inchr1', 'incja6', 'incjb4', 'incjb6', 'incjc6', 'incjd6', 'incje6', 'incjf6', 'incjh6', 'incji6',
                   'incjj6', 'incjn6', 'incjo6', 'incjs6', 'inclk6', 'inclu6', 'inclx6', 'incmb1', 'incml6', 'incnb1',
                   'incnc6', 'incnn1', 'incoa6', 'incoh4', 'incok1', 'incok4', 'incok6', 'incol1', 'incoo1', 'incop6',
                   'incpc6', 'incpl6', 'incpr6', 'incrl6', 'incrn1', 'incrw6', 'incrxb', 'incsp6', 'incsv6', 'incti1',
                   'incum1', 'indae4', 'indah1', 'indai4', 'indam1', 'indam4', 'indar6', 'indbd4', 'indbs6', 'inddl6',
                   'indea6', 'inded4', 'indef6', 'indeg1', 'indeh6', 'indei6', 'indej6', 'indel4', 'indel5', 'indem6',
                   'inden6', 'indep4', 'inder6', 'indes6', 'indet6', 'indeu6', 'indew6', 'indgi6', 'indgt6', 'indha6',
                   'indhbb', 'indhlb', 'indhm4', 'indhn1', 'indhp1', 'indhr1', 'indhu1', 'indib4', 'indid6', 'indig1',
                   'indig6', 'indit6', 'indiu1', 'indiu4', 'indiv1', 'indlab', 'indlh6', 'indli2', 'indlob', 'indlub',
                   'indma1', 'indmrb', 'indmt1', 'indmu4', 'indpc4', 'indpr6', 'indrc6', 'indrgb', 'indrk1', 'indrl1',
                   'indru6', 'indsk1', 'indsm6', 'indtw1', 'indur6', 'indwa1', 'indwkb', 'indwn6', 'indwr6', 'inenr1',
                   'inerp6', 'inerv6', 'inesh1', 'infbd6', 'infbe6', 'infbm6', 'infbp6', 'infbrb', 'infbs6', 'infch5',
                   'inflt6', 'infma6', 'infmh6', 'infmj6', 'infms6', 'ingaib', 'ingalb', 'ingao6', 'ingas6', 'ingau1',
                   'ingau2', 'ingau4', 'ingau5', 'ingaw2', 'ingay4', 'ingdl6', 'ingdm6', 'ingdp6', 'inged2', 'ingga1',
                   'inggb6', 'inggc6', 'inggd6', 'ingge6', 'inggf6', 'inggg6', 'inggi6', 'inggl6', 'inggm6', 'inggn2',
                   'inggo6', 'inggp6', 'inggs6', 'inggu6', 'inggv1', 'ingha1', 'inghc6', 'inghpb', 'inghr6', 'inghwb',
                   'ingid6', 'ingin6', 'ingjib', 'ingjxb', 'ingkj2', 'ingkjb', 'ingly6', 'ingmi6', 'ingna6', 'ingnc6',
                   'ingng6', 'ingnl6', 'ingnp6', 'ingnr6', 'ingnt6', 'ingoi4', 'ingop4', 'ingpb6', 'ingpr1', 'ingrd6',
                   'ingrl6', 'ingrn6', 'ingrr6', 'ingrs6', 'ingrw6', 'ingtgb', 'ingti6', 'ingtr2', 'ingts6', 'ingtzb',
                   'ingux4', 'ingwl4', 'ingwl6', 'ingwm4', 'inhal1', 'inhan6', 'inhao6', 'inhas6', 'inhbb6', 'inhbx4',
                   'inhdd6', 'inheb6', 'inhei6', 'inhem6', 'inhglb', 'inhgt1', 'inhir6', 'inhjr4', 'inhld2', 'inhle6',
                   'inhlib', 'inhnd1', 'inhon1', 'inhpi6', 'inhrn1', 'inhsf6', 'inhsp6', 'inhss4', 'inhst6', 'inhsu6',
                   'inhtsb', 'inhur6', 'inhwr1', 'inhyb6', 'inhyd4', 'inhyd5', 'inhyd6', 'inhza1', 'inhza6', 'inidr4',
                   'inidr6', 'inigu6', 'inilp6', 'inimf4', 'ininb6', 'inind6', 'inini6', 'ininn6', 'inint6', 'inisk4',
                   'inisk6', 'inixa4', 'inixb4', 'inixc4', 'inixd4', 'inixe1', 'inixe4', 'inixg4', 'inixh4', 'inixi4',
                   'inixj4', 'inixk4', 'inixl4', 'inixl5', 'inixm4', 'inixm6', 'inixn4', 'inixp4', 'inixq4', 'inixr4',
                   'inixs4', 'inixt4', 'inixu4', 'inixw4', 'inixw6', 'inixy1', 'inixy4', 'inixy6', 'inixz1', 'inixz4',
                   'injai4', 'injai5', 'injai6', 'injak1', 'injal6', 'injayb', 'injbd1', 'injbl6', 'injbnb', 'injda1',
                   'injdh4', 'injdh6', 'injga4', 'injgb4', 'injgd1', 'injgi6', 'injha6', 'injhob', 'injhv6', 'injigb',
                   'injjk6', 'injka6', 'injlr4', 'injnj6', 'injnr4', 'injnr6', 'injpgb', 'injpi6', 'injpv6', 'injpw6',
                   'injrh4', 'injsa4', 'injsg6', 'injsm6', 'injsz6', 'injtp1', 'injuc6', 'injux6', 'injwab', 'inkak1',
                   'inkak6', 'inkal1', 'inkap6', 'inkar6', 'inkat1', 'inkbc6', 'inkbt1', 'inkcg6', 'inkdd6', 'inkdi1',
                   'inkdl6', 'inkdn1', 'inkdp1', 'inkelb', 'inkgg6', 'inkgj1', 'inkhd6', 'inkiw1', 'inkja6', 'inkjb6',
                   'inkjd6', 'inkjg6', 'inkjh6', 'inkjib', 'inkjm6', 'inkjr6', 'inkkr1', 'inkku6', 'inklb6', 'inklc6',
                   'inklg6', 'inklh4', 'inkli6', 'inklk6', 'inklm6', 'inkln6', 'inkls6', 'inkly1', 'inkmab', 'inkmb1',
                   'inkmi6', 'inkml6', 'inknd1', 'inknk6', 'inknlb', 'inknu4', 'inknu5', 'inknu6', 'inkoc5', 'inkod1',
                   'inkoi1', 'inkok1', 'inkon1', 'inkpk6', 'inkri1', 'inkrk1', 'inkrm6', 'inkrn1', 'inkrp1', 'inkrw1',
                   'inksg1', 'inksh1', 'inksp1', 'inktd1', 'inktgb', 'inkti1', 'inktrb', 'inktt6', 'inktu4', 'inktu6',
                   'inktw1', 'inkty6', 'inkuk1', 'inkuk6', 'inkur6', 'inkuu4', 'inkvi1', 'inkvl1', 'inkvr6', 'inkvt1',
                   'inkwab', 'inkwgb', 'inkwhb', 'inkxj2', 'inkym6', 'inkze6', 'inkzp6', 'inkzt6', 'inlch6', 'inlda4',
                   'inldh6', 'inlglb', 'inlko4', 'inlkqb', 'inlon6', 'inlpb6', 'inlpc6', 'inlpd6', 'inlpg6', 'inlpi6',
                   'inlpj6', 'inlpm6', 'inlpr1', 'inlps6', 'inlpw6', 'inltbb', 'inlud6', 'inluh4', 'inluh5', 'inluh6',
                   'inlwg6', 'inmaa1', 'inmaa4', 'inmaa5', 'inmaa6', 'inmab6', 'inmae6', 'inmah1', 'inmai6', 'inmal1',
                   'inmap1', 'inmaq6', 'inmas6', 'inmbc6', 'inmbd6', 'inmbs6', 'inmci1', 'inmda1', 'inmdd6', 'inmde6',
                   'inmdg6', 'inmdk1', 'inmdp1', 'inmdu6', 'inmdv1', 'inmdw1', 'inmea6', 'inmec6', 'inmghb', 'inmgr1',
                   'inmha1', 'inmhdb', 'inmhe1', 'inmhgb', 'inmhn2', 'inmkcb', 'inmkd6', 'inmli1', 'inmlp1', 'inmlw1',
                   'inmnb2', 'inmnr1', 'inmnub', 'inmnw1', 'inmoh4', 'inmor2', 'inmpc1', 'inmpr6', 'inmqk6', 'inmra1',
                   'inmrd1', 'inmreb', 'inmrg4', 'inmrj6', 'inmrm1', 'inmsr6', 'inmtw1', 'inmuc6', 'inmul6', 'inmun1',
                   'inmur1', 'inmuz6', 'inmwa6', 'inmyb1', 'inmyl6', 'inmyo6', 'inmyq4', 'inmza4', 'inmzu4', 'innag4',
                   'innag6', 'innan1', 'innav1', 'innda6', 'inndc4', 'inndg1', 'inndp1', 'innee1', 'innel1', 'inngb6',
                   'inngkb', 'inngo6', 'inngp6', 'inngrb', 'inngsb', 'innki6', 'innknb', 'innml1', 'innmtb', 'innnn6',
                   'innpgb', 'innpt1', 'innrp6', 'innsa1', 'innsk6', 'inntlb', 'inntvb', 'innur6', 'innvb1', 'innvp1',
                   'innvt1', 'innvy4', 'innwp1', 'innyp6', 'inokh1', 'inomn4', 'inomu1', 'inonj1', 'inpab4', 'inpak6',
                   'inpan1', 'inpao6', 'inpap2', 'inpat4', 'inpav1', 'inpav2', 'inpbd1', 'inpbd4', 'inpblb', 'inpdd1',
                   'inpek6', 'inpgh4', 'inphbb', 'inpid1', 'inpin1', 'inpit6', 'inpkd6', 'inpkr6', 'inpmb1', 'inpmp6',
                   'inpmt6', 'inpnb6', 'inpne6', 'inpnf5', 'inpni6', 'inpnj1', 'inpnk6', 'inpnl6', 'inpnm1', 'inpnn1',
                   'inpnp6', 'inpnq2', 'inpnq4', 'inpnq6', 'inpntb', 'inpnu6', 'inpnv6', 'inpny1', 'inpny4', 'inpny6',
                   'inppg6', 'inppj1', 'inprd6', 'inprg1', 'inprk6', 'inprt1', 'inpsh1', 'inpsi6', 'inpsn6', 'inpsp6',
                   'inptl6', 'inptn1', 'inptpb', 'inpua6', 'inpue6', 'inpui6', 'inpul1', 'inpum6', 'inpun6', 'inpur1',
                   'input4', 'inpvl6', 'inpvs6', 'inpwl6', 'inpyb4', 'inpys6', 'inqrp6', 'inqui1', 'inrai6', 'inraj4',
                   'inraj6', 'inram1', 'inrdp2', 'inrea6', 'inred1', 'inrew4', 'inrgbb', 'inrgh4', 'inrgj2', 'inrgt1',
                   'inrgub', 'inrja4', 'inrji4', 'inrjn6', 'inrjp1', 'inrjr1', 'inrkg1', 'inrmd4', 'inrml6', 'inrnc5',
                   'inrng2', 'inrnr1', 'inrpl6', 'inrpr4', 'inrpr6', 'inrpu5', 'inrri1', 'inrrk4', 'inrtc1', 'inrtc4',
                   'inrtm6', 'inrup4', 'inrvd1', 'inrwr1', 'inrxlb', 'insabb', 'insac6', 'insaj6', 'insal1', 'insas6',
                   'insau6', 'insbc6', 'insbh1', 'insbi6', 'insbk6', 'insbl6', 'insbw6', 'insbz1', 'insch6', 'insgf6',
                   'inshi1', 'inshl4', 'inshp1', 'insik1', 'insjr6', 'inskd6', 'inskpb', 'insll6', 'inslr2', 'inslrb',
                   'inslt6', 'inslv4', 'insmk6', 'insmpb', 'insmr1', 'insna6', 'insnbb', 'insnf6', 'insng2', 'insni6',
                   'insnlb', 'insnn6', 'insnr6', 'insns6', 'inspc6', 'inspe6', 'insre6', 'insrk6', 'insrv1', 'insse4',
                   'instfb', 'instib', 'instm6', 'instp1', 'instrb', 'instt6', 'instu6', 'instv1', 'instv4', 'instv6',
                   'inswd1', 'insxe6', 'insxr4', 'insxr5', 'insxv4', 'insxv6', 'intad1', 'intas6', 'intbc6', 'intbm6',
                   'intbp6', 'intbs6', 'intbt6', 'intcr6', 'intde6', 'intei4', 'intel1', 'inten6', 'intez4', 'intgn6',
                   'intha6', 'inthl1', 'intho6', 'intir4', 'intiv1', 'intja1', 'intjpb', 'intjv4', 'intkd2', 'intkd6',
                   'intknb', 'intlg6', 'intlt6', 'intmi6', 'intmp1', 'intmx6', 'intna1', 'intnc6', 'intnd1', 'intngb',
                   'intni6', 'intnk1', 'intns6', 'intph1', 'intpj6', 'intpn1', 'intra1', 'intrl6', 'intrp1', 'intrv4',
                   'intrz4', 'intsi6', 'inttp6', 'intts1', 'intui6', 'intun1', 'intup6', 'intut1', 'intut6', 'intvc6',
                   'intvt6', 'intyr1', 'inudi6', 'inudn6', 'inudr4', 'inudr6', 'inudz6', 'inukl6', 'inulpb', 'inulw1',
                   'inumb1', 'inumr1', 'inurf6', 'inurg6', 'inuri6', 'inurt6', 'inutn1', 'invad1', 'inval6', 'invap1',
                   'inven1', 'invep1', 'invga4', 'invga5', 'invgr6', 'invkh6', 'invkm1', 'invld6', 'invln6', 'invlr6',
                   'invng1', 'invns4', 'invns5', 'invns6', 'invpi6', 'invrd1', 'invru1', 'invsa6', 'invsi1', 'invsk6',
                   'invsp6', 'invsv1', 'invtc6', 'invtz1', 'invtz4', 'invtz6', 'invva1', 'invyd1', 'invzj1', 'invzm6',
                   'invzr6', 'inwal6', 'inwfd6', 'inwfi6', 'inwft6', 'inwgc4', 'inwrr6', 'inyma6', 'inyna6', 'inynk6',
                   'inynl6', 'inynm6', 'inynt6', 'inzip6','noi001']

valid_gst_rate_list = ['0', '0.00', '0.0', '0.1', '0.25', '1', '1.5', '3', '5', '7.5', '12', '18', '28']

full_form_invoice_category = {
    "txn": "tax invoice", "cdn": "credit note", "ddn": "debit note", "exp": "export", "vch": "voucher","imp":"import","cdn": "c", "ddn": "d", "dc": "delivery challan"
}

full_form_invoice_category_all = {
    "txn": "tax invoice", "cdn": "credit note", "ddn": "debit note", "exp": "export", "vch": "voucher","imp":"import"
}
gstr1_delete_fields = [
    {
        'name': 'supplier_gstin',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
    {
        'name': 'document_number',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    },
    {
        'name': 'document_date',
        'mandate': True,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'invoice_status',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["add", "d"]}}]
    }
]
gstr2_delete_fields = [
    {
        'name': 'buyer_gstin',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
    {
        'name': 'document_number',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    },
    {
        'name': 'document_date',
        'mandate': True,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'invoice_status',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["add", "d"]}}]
    }
]

gstr1_invoice_status_c__mandate_fields = ['supplier_gstin', 'document_number', 'document_date', 'supply_type', 'invoice_status', 'invoice_category']

gstr1_fields = [{
    'name': 'supplier_gstin',
    'mandate': True,
    'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
    {
        'name': 'buyer_gstin',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}],
    },

    {
        'name': 'port_code',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_port_code}}]
    },
    {
        'name': 'customer_name',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'alpha_check'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'valid_in',
                    'kwargs': {'list_to_be_checked': ["nor", "emp", "nrt", "ngt"],'error_message': ["Normal", 'Exempted', 'Nil-Rated', 'Non-Gst']},
                    }]
    },
    # {
    #     'name': 'gst_rate',
    #     'mandate': True,
    #     'checks': [{'method': 'valid_in',
    #                 'kwargs': {'list_to_be_checked': valid_gst_rate_list}}]
    # },
    {
        'name': 'document_number',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    },
    {
        'name': 'document_date',
        'mandate': True,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {},
                    'message': 'Invoice date should not be future date / invalid date ( format dd-mm-yyyy or dd/mm/yyyy)'},
                   {'method': 'future_date_check', 'kwargs': {},
                    'message': 'Invoice date should not be future date / invalid date ( format dd-mm-yyyy or dd/mm/yyyy)'}]
    },
    # {
    #     'name': 'ERP_document_number',
    #     'mandate': False,
    #     'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
    #                {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    # },
    {
        'name': 'ERP_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}},
                   {'method': 'future_date_check', 'kwargs': {}}]
    },
    {
        'name': 'isamended',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'reverse_charge',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'place_of_supply',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_state_code}}]
    },
    {
        'name': 'invoice_category',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {
            'list_to_be_checked': ["txn", "cdn", "ddn", "exp", "vch", "dc"]}}]
    },
    {
        'name': 'invoice_status',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["add", "d", "c"]}}]
    },
    {
        'name': 'total_invoice_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'txpd_taxtable_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'total_taxable_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'shipping_bill_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}},
                   {'method': 'compare_date', 'kwargs': {},
                    'message': 'shipping_bill_date should be greater than document_date'}]
    },
    {
        'name': 'shipping_bill_number',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 3, 'max_len': 7}}]
    },
    {
        'name': 'amended_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': 'original_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}}]
    },
    {
        'name': 'original_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}}]
    },
    {
        'name': 'original_month',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': 'gstr3b_return_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': '3b_auto_fill_period',
        'mandate': False,
        'checks': [{'method': 'gstr3b_validate_period', 'kwargs': {},
                   'message': ' should be of valid type / format(mm-yyyy)'}]
    },
    {
        'name': 'gstr1_return_period',
        'mandate': False,
        'checks': [{'method': 'gstr_validate_period', 'kwargs': {},
                   'message': ' should be of valid format(mm-yyyy)'}]
    },
    {
        'name': 'isamended',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                             [
                                # {'field_name': 'amended_period', 'checks': []},
                              {'field_name': 'original_document_number', 'checks': []},
                              {'field_name': 'original_document_date', 'checks': []}],
                         'field_name': 'isamended', 'field_value': 'y'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['wopay', 'wpay', 'exp']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'exp'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': ['rfv', 'rcv']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'vch'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de', 'wopay', 'wpay','b2b', 'b2cs',
                                                           'b2cl', 'cdn']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'cdn'},
                    'kwargs_api':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de', 'wopay', 'wpay','b2b', 'b2cs',
                                                           'b2cl', 'cdn', 'r']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'cdn'}
                    }]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de', 'wpay', 'wopay','b2b', 'b2cs',
                                                           'b2cl', 'cdn']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'ddn'},
                    'kwargs_api':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de', 'wpay', 'wopay','b2b', 'b2cs',
                                                           'b2cl', 'cdn', 'r']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'ddn'}
                    }]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': ['sewop', 'sewp', 'de', 'r', 'b2b', 'b2cl','b2cs']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'txn'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': ['job_work', 'others','supply_of_liquid_gas', 'supply_on_approval']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'dc'}}]
    },
    {
        'name': 'sale_through_ecommerce_operator',
        'mandate': False,
        'checks': [{'method': 'validate_y', 'kwargs': {},
                   'message': 'sale_through_ecommerce_operator should be either Y/y or N/n'}]
    },
    {
        'name': 'amortised_cost',
        'mandate': False,
        'checks': [{'method': 'validate_y_yes', 'kwargs': {},
                   'message': 'amortised_cost should be either Y/y or N/n or yes/no or YES/NO'}]
    },
    {
        'name': 'sale_through_ecommerce_operator',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'etin',
                                'label_name': 'etin',
                                'extra_check': True,
                                'mandate': True,
                                'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}, 
                                            'message': 'If sale_through_ecommerce_operator is Y, then etin is mandatory and it should be of valid type.'}]
                            }],
                            'field_name': 'sale_through_ecommerce_operator', 'field_value': 'y'}}]
    },
]
gstr1_voucher_items_field = [
    {
        'name': 'hsn_code',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 4, 'max_len': 8}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'hsn_check'}}]
    },
    {
        'name': 'unit_of_product',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_uqc_code}}]
    },
    {
        'name': 'product_name',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'alpha_check'}}]
    },
    {
        'name': 'taxable_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': ' should be of valid type. Upto 2 decimal allowed'}]
    },
    {
        'name': 'itc_elgibity',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['n', 'N', 'is', 'IS', 'IN', 'in', 'cd', 'CD']}}]
    },
    {
        'name': 'cess_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'sgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'cgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'igst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'quantity',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'quantity'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nor'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'emp'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nrt'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'ngt'}}]
    },
]

gstr1_items_field = [
    {
        'name': 'hsn_code',
        'mandate': True,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 4, 'max_len': 8}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'hsn_check'}}]
    },
    {
        'name': 'unit_of_product',
        'mandate': True,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_uqc_code}}]
    },
    {
        'name': 'product_name',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'alpha_check'}}]
    },
    {
        'name': 'taxable_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': ' should be of valid type. Upto 2 decimal allowed'}]
    },
    {
        'name': 'invoice_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': ' should be of valid type. Upto 2 decimal allowed'}]
    },
    {
        'name': 'itc_elgibity',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['n', 'N', 'is', 'IS', 'IN', 'in', 'cd', 'CD']}}]
    },
    {
        'name': 'cess_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'sgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'cgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'igst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'quantity',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'quantity'}}]
    },
    {
        'name': 'gst_rate',
        'mandate': False,
        'checks': [{'method': 'valid_in',
                    'kwargs': {'list_to_be_checked': valid_gst_rate_list}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nor'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'emp'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nrt'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'ngt'}}]
    },
]

inter_mandate = [{
    'name': 'igst_amount',
    'mandate': True,
    'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
}]
intra_mandate = [{
    'name': 'cgst_amount',
    'mandate': True,
    'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
},
    {
        'name': 'sgst_amount',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    }
]

inter_mandate_two = [{
    'name': 'igst_amount',
    'mandate': False,
    'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['0', '', '0.0', None]}}]
}]
intra_mandate_two = [{
    'name': 'cgst_amount',
    'mandate': False,
    'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['0', '', '0.0', None]}}]
},
    {
        'name': 'sgst_amount',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['0', '', '0.0', None]}}]
    }
]

supply_type_conditons = {
    ('nor', 'inter'): inter_mandate,
    ('emp', 'inter'): inter_mandate_two,
    ('ngt', 'inter'): inter_mandate_two,
    ('nrt', 'inter'): inter_mandate_two,
    ('nor', 'intra'): intra_mandate,
    ('emp', 'intra'): intra_mandate_two,
    ('ngt', 'intra'): intra_mandate_two,
    ('nrt', 'intra'): intra_mandate_two
}

gstr1_item = openapi.Schema(type=openapi.TYPE_OBJECT,
                            properties={
                                'hsn_code': openapi.Parameter('hsn_code',
                                                              openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING,
                                                              description='string',
                                                              required=True),
                                'quantity': openapi.Parameter('quantity',
                                                              openapi.IN_BODY,
                                                              type=openapi.FORMAT_DOUBLE,
                                                              description='It accepts decimal value accurate to two decimal places',
                                                              required=True),
                                'unit_of_product': openapi.Parameter('unit_of_product',
                                                                     openapi.IN_BODY,
                                                                     type=openapi.TYPE_STRING,
                                                                     description='string',
                                                                     required=False),
                                'gst_rate': openapi.Parameter('gst_rate',
                                                              openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING,
                                                              description='string',
                                                              required=True),
                                'cess_amount': openapi.Parameter('cess_amount',
                                                                 openapi.IN_BODY,
                                                                 type=openapi.FORMAT_DOUBLE,
                                                                 description='It accepts decimal value accurate to two decimal places',
                                                                 required=False),
                                'taxable_value': openapi.Parameter('taxable_value',
                                                                   openapi.IN_BODY,
                                                                   type=openapi.FORMAT_DOUBLE,
                                                                   description='It accepts decimal value accurate to two decimal places',
                                                                   required=True),
                                'txpd_taxable_amount': openapi.Parameter(
                                    'txpd_taxable_amount', openapi.IN_BODY,
                                    type=openapi.FORMAT_DOUBLE,
                                    description='It accepts decimal value accurate to two decimal places',
                                    required=False),
                                'item_description': openapi.Parameter('item_description',
                                                                      openapi.IN_BODY,
                                                                      type=openapi.TYPE_STRING,
                                                                      description='string',
                                                                      required=True),
                                'product_name': openapi.Parameter('product_name',
                                                                  openapi.IN_BODY,
                                                                  type=openapi.TYPE_STRING,
                                                                  description='string',
                                                                  required=True)
                            })

gstr_1_data = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'document_number': openapi.Parameter('document_number', openapi.IN_BODY, description="Invoice Number",
                                             type=openapi.TYPE_STRING, required=True),
        'document_date': openapi.Parameter('document_date', openapi.IN_BODY,
                                           description="Invoice Date;It accepts date in the format d-%m-%Y",
                                           type=openapi.TYPE_STRING, required=True),
        'original_document_number': openapi.Parameter('original_document_number', openapi.IN_BODY,
                                                      description="Original Invoice Number; This field is mandatory if the isameded key is 'Y' ",
                                                      type=openapi.TYPE_STRING, required=False),
        'original_document_date': openapi.Parameter('original_document_date', openapi.IN_BODY,
                                                    description="Original Invoice Date; This field is mandatory if the isameded key is 'Y'.It accepts date in the format d-%m-%Y",
                                                    type=openapi.TYPE_STRING, required=False),
        'ref_document_number': openapi.Parameter('ref_document_number', openapi.IN_BODY,
                                                 description="Reference Invoice Number",
                                                 type=openapi.TYPE_STRING, required=False),
        'ref_document_date': openapi.Parameter('ref_document_date', openapi.IN_BODY,
                                               description="Reference Invoice Date; It accepts date in the format d-%m-%Y",
                                               type=openapi.TYPE_STRING, required=False),

        'supply_type': openapi.Parameter('supply_status', openapi.IN_BODY,
                                         description="Supply Type; Possible Values-: Normal, Exempted, Nil-Rate, Non-Gst",
                                         type=openapi.TYPE_STRING, required=True),
        'invoice_status': openapi.Parameter('invoice_status', openapi.IN_BODY,
                                            description="Invoice Status;Possible Values-: Add, D ",
                                            type=openapi.TYPE_STRING, required=True),
        'invoice_category': openapi.Parameter('invoice_category', openapi.IN_BODY,
                                              description="Invoice Category;Possible Values-: Tax Invoice, Credit Note, Debit Note, Export, Voucher ",
                                              type=openapi.TYPE_STRING, required=True),
        'invoice_type': openapi.Parameter('invoice_type', openapi.IN_BODY, description="Invoice Type",
                                          type=openapi.TYPE_STRING,
                                          required=True),
        'net_amount': openapi.Parameter('net_amount', openapi.IN_BODY,
                                        description="Invoice/Note/Voucher value.It accepts decimal value accurate to two decimal places",
                                        type=openapi.TYPE_NUMBER, required=True, format=openapi.FORMAT_DOUBLE),
        'taxtable_value': openapi.Parameter('taxable_value', openapi.IN_BODY,
                                            description="Gross advance received(Excluding tax)/Taxable Value.It accepts decimal value accurate to two decimal places",
                                            type=openapi.FORMAT_DOUBLE, required=False),
        'shipping_bill_number': openapi.Parameter('shipping_bill_number', openapi.IN_BODY,
                                                  description="Shipping Bill Number",
                                                  type=openapi.TYPE_STRING, required=False),
        'shipping_bill_date': openapi.Parameter('shipping_bill_date', openapi.IN_BODY,
                                                description="Shipping Bill Date; It accepts date in the format d-%m-%Y",
                                                type=openapi.TYPE_STRING, required=False),
        'reason': openapi.Parameter('reason', openapi.IN_BODY, description="Reason for Amending the invoice",
                                    type=openapi.TYPE_STRING, required=False),
        'port_code': openapi.Parameter('port_code', openapi.IN_BODY, description="Port Code", type=openapi.TYPE_STRING,
                                       required=False),
        'location': openapi.Parameter('location', openapi.IN_BODY, description="Location", type=openapi.TYPE_STRING,
                                      required=False),
        'gstr1_return_period': openapi.Parameter('gstr1_return_period', openapi.IN_BODY,
                                                 description="Gstr1 Return Period (it should be in the format month-year eg. {05-2020, 01-2019})",
                                                 type=openapi.TYPE_STRING, required=False),
        'gstr3b_return_period': openapi.Parameter('gstr3b_return_period', openapi.IN_BODY,
                                                  description="Gstr3B Return Period (it should be in the format month-year eg. {05-2020, 01-2019})",
                                                  type=openapi.TYPE_STRING, required=False),

        'reverse_charge': openapi.Parameter('reverse_charge', openapi.IN_BODY,
                                            description="Reverse charge; It accepts only 'Y' or 'N'",
                                            type=openapi.TYPE_STRING,
                                            required=True),
        'isamended': openapi.Parameter('isamended', openapi.IN_BODY,
                                       description="Amended Period; This field is mandatory if isamended is 'Y'. Send Y if the invoice is amended else send N ",
                                       type=openapi.TYPE_STRING, required=False),

        'place_of_supply': openapi.Parameter('place_of_supply', openapi.IN_BODY,
                                             description="Place Of Supply; It should be valid state code.",
                                             type=openapi.TYPE_STRING, required=True),
        'supplier_gstin': openapi.Parameter('supplier_gstin', openapi.IN_BODY, description="Supplier GSTIN",
                                            type=openapi.TYPE_STRING, required=True),
        'buyer_gstin': openapi.Parameter('buyer_gstin', openapi.IN_BODY, description="Buyer GSTIN",
                                         type=openapi.TYPE_STRING,
                                         required=False),
        'customer_name': openapi.Parameter('customer_name', openapi.IN_BODY, description="Name of the customer",
                                           type=openapi.TYPE_STRING,
                                           required=False),
        'itemList': openapi.Parameter('itemList', openapi.IN_BODY, description="List of line items",
                                      items=gstr1_item,
                                      type=openapi.TYPE_ARRAY, required=True)
    })

data = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'purchaseData': openapi.Parameter('purchaseData', openapi.IN_BODY, description="List of Invoices",
                                          items=gstr_1_data, type=openapi.TYPE_ARRAY, required=True)
    }
)
preparing_response_format = {**gstr_1_data.properties}
preparing_response_format["error"] = openapi.Schema(type=openapi.TYPE_OBJECT,
                                                    properties={})
preparing_response_format["itemList"] = openapi.Schema(type=openapi.TYPE_OBJECT,
                                                       properties={**gstr1_item.properties,
                                                                   "error": openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                                           properties={})
                                                                   })

gstr1_response = {200: openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'purchaseData': openapi.Parameter('purchaseData', openapi.IN_BODY, description="List of Invoices",
                                          items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                               properties=preparing_response_format),
                                          type=openapi.TYPE_ARRAY)
    }
)}
# 'success_count': openapi.Parameter('success_count', openapi.IN_BODY, description="List of invoices successfully saved.",
#                                    type=openapi.TYPE_NUMBER, required=True),
# 'failure_count': openapi.Parameter('failure_count', openapi.IN_BODY,
#                                    description="List of invoices failed to save in the database.",
#                                    type=openapi.TYPE_NUMBER, required=True),
# 'status': openapi.Parameter('status', openapi.IN_BODY,
#                             description="It can be partial or complete, if there is any error in saving invoices it will be partial else complete.",
#                             type=openapi.TYPE_NUMBER, required=True),
gstr2_fields = [
    {
        'name': 'supplier_gstin',
        'mandate': False,
        'extra_check': True,
        'checks': [{'method': 'check_for_supplier_gstin', 'kwargs': {},
                    'message': " should be of valid type."}]
    },
    {
        'name': 'sez_gstin',
        'mandate': False,
        'extra_check': True,
        'checks': [{'method': 'check_for_sez_gstin', 'kwargs': {},
                    'message': "Sez Gstin is Mandatory if Is Sez is Y"}]
    },

    {
        'name': 'customer_name',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'alpha_check'}}]
    },
    {
        'name': 'reverse_charge',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'port_code',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_port_code}}]
    },
    {
        'name': 'txpd_taxtable_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'inv_itc_elgibity',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'yes', 'n', 'ip', 'is', 'cp', 'no']}}]
    },

    {
        'name': 'buyer_gstin',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'valid_in',
                    'kwargs': {'list_to_be_checked': ["nor", "emp", "nrt", "ngt"],'error_message': ["Normal", 'Exempted', 'Nil-Rated', 'Non-Gst']},
                    } ]
    },
    {
        'name': 'document_number',
        'mandate': True,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16},'message': "Invoice no/Note no/Bill of entry no. should not exceed 16 characters"},{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number2'}}]
    },
    {
        'name': 'document_date',
        'mandate': True,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {},
                    'message': 'Invoice date should not be future date / invalid date ( format dd-mm-yyyy or dd/mm/yyyy)'}]
    },
    # {
    #     'name': 'ERP_document_number',
    #     'mandate': False,
    #     'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
    #                {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    # },
    {
        'name': 'ERP_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}},
                   {'method': 'future_date_check', 'kwargs': {}}]
    },
    {
        'name': 'isamended',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'issez',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'payment_status',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n', 'P', 'p']}}]
    },
    {
        'name': 'paid_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    # {
    #     'name': 'reverse_charge',
    #     'mandate': True,
    #     'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    # },
    {
        'name': 'place_of_supply',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_state_code}}]
    },
    {
        'name': 'invoice_category',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {
            'list_to_be_checked': ["txn", "cdn", "ddn", "imp", "vch", "isd"]}}]
    },

    {
        'name': 'invoice_status',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["add", "d"]}}]
    },

    {
        'name': 'total_invoice_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'total_taxable_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'shipping_bill_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}},
                   {'method': 'compare_date', 'kwargs': {},
                    'message': 'shipping_bill_date should be greater the document_date'}]
    },
    {
        'name': 'shipping_bill_number',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 3, 'max_len': 7}}]
    },
    {
        'name': 'amended_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': 'original_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}}]
    },
    {
        'name': 'original_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}}]
    },
    {
        'name': 'gstr3b_return_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': '3b_auto_fill_period',
        'mandate': False,
        'checks': [{'method': 'gstr3b_validate_period', 'kwargs': {},
                    'message': ' should be of valid type / format(mm-yyyy / mmyyyy)'}]
    },
    {
        'name': 'gstr2_return_period',
        'mandate': False,
        'checks': [{'method': 'gstr_validate_period', 'kwargs': {},
                   'message': ' should be of valid format(mm-yyyy)'}]
    },
    {
        'name': 'isamended',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                             [
                                 # {'field_name': 'amended_period', 'checks': []},
                              {'field_name': 'original_document_number', 'checks': []},
                              {'field_name': 'original_document_date', 'checks': []}],
                         'field_name': 'isamended', 'field_value': 'y'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [
                                    {'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['impg', 'impg_sez', 'imps', 'imps_sez']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'imp'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': ['rfv', 'rcv']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'vch'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de','ur',
                                                           'r', 'impg', 'impg_sez','imps', 'imps_sez','b2b','b2cs']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'cdn'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in', 'kwargs': {
                                    'list_to_be_checked': ['sewop', 'sewp', 'de',
                                                           'ur', 'r', 'impg', 'impg_sez', 'imps', 'imps_sez','b2b','b2cs']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'ddn'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked':  ['r', 'de', 'sewp', 'sewop']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'txn'}}]
    },
    {
        'name': 'invoice_category',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'invoice_type',
                                'label_name': 'invoice_type',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked':  ['isdi', 'isdc']}}]
                            }],
                            'field_name': 'invoice_category', 'field_value': 'isd'}}]
    },
    {
        'name': 'reverse_charge',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'supplier_gstin',
                                'label_name': 'supplier_gstin',
                                'checks': []
                            }],
                            'field_name': 'reverse_charge', 'field_value': 'n'}}]
    },
    {
        'name': 'gstr7_return_period',
        'mandate': False,
        'checks': [{'method': 'gstr_validate_period', 'kwargs': {},
                   'message': ' should be of valid format(mm-yyyy)'},
                   {'method': 'past_return_period_check', 'kwargs': {},
                   'message': 'should be valid month and year and should not be past months and years'}]
    },
    {
        'name': 'gstr7_amend_type',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["rejected by deductee", "uploaded by deductor"]}}]
    },
    {
        'name': 'original_gstin_of_supplier',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
]

gstr2_items_field = [
    {
        'name': 'hsn_code',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 4, 'max_len': 8}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'hsn_check'}}]
    },
    {
        'name': 'unit_of_product',
        'mandate': True,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_uqc_code}}]
    },
    {
        'name': 'product_name',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'alpha_check'}}]
    },
    {
        'name': 'taxable_value',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': ' should be of valid type. Upto 2 decimal allowed'}]
    },
    {
        'name': 'assessable_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': 'Assessable Value should be of valid type. Upto 2 decimal allowed'}]
    },
    {
        'name': 'itc_elgibity',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['n', 'N', 'is', 'IS', 'IN', 'in', 'cp', 'CP']}}]
    },
    {
        'name': 'cess_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'sgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'cgst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'igst_amount',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'quantity',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'quantity'}}]
    },
    {
        'name': 'gst_rate',
        'mandate': False,
        'checks': [{'method': 'valid_in',
                    'kwargs': {'list_to_be_checked': valid_gst_rate_list}}]
    },
    {
        'name': 'igst_tds',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'cgst_tds',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'sgst_tds',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'original_taxable_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nor'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'emp'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'nrt'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                            [{
                                'field_name': 'gst_rate',
                                'label_name': 'gst_rate',
                                'checks': [{'method': 'valid_in',
                                            'kwargs': {'list_to_be_checked': valid_gst_rate_list }}],
                                'mandatory': False
                            }],
                            'field_name': 'supply_type', 'field_value': 'ngt'}}]
    },
]

error_constant_mandatory = {'document_number': 'GDM01', 'document_date': 'GDM02', 'original_document_number': 'GOM01',
                            'original_document_date': 'GOM02', 'ref_document_number': 'GRM01',
                            'ref_document_date': 'GRM02','original_month': 'GOV03',
                            'supply_type': 'GSM01', 'invoice_status': 'GIM01', 'invoice_category': 'GIM02',
                            'invoice_type': 'GIM03',
                            'total_invoice_value': 'GTM01', 'total_taxable_value': 'GTM02',
                            'txpd_taxtable_value': 'GTM03',
                            'shipping_bill_number': 'GSM02', 'shipping_bill_date': 'GSM03', 'reason': 'GRM03',
                            'port_code': 'GPM01',
                            'location': 'GLM01', 'gstr1_return_period': 'GGM01', 'gstr3b_return_period': 'GGM02',
                            'reverse_charge': 'GRM04','issez':'GIM04',
                            'isamended': 'GIM04', 'amended_pos': 'GAM05', 'amended_period': 'GAM06',
                            'place_of_supply': 'GPM02',
                            'supplier_gstin': 'GSM04', 'buyer_gstin': 'GBM01', 'customer_name': 'GCM01',
                            'itemList': 'GIM05',
                            'igst_amount': 'GIMI01', 'cgst_amount': 'GIMC01', 'sgst_amount': 'GIMS01',
                            'taxable_value': 'GIMT01',
                            'hsn_code': 'GIMH01', 'product_name': 'GIPH01', 'item_description': 'GIMI02',
                            'quantity': 'GIMQ01',
                            'cess_amount': 'GIMC02', 'gst_rate': 'GIMG01', 'unit_of_product': 'GIMU01',
                            'itc_elgibity': 'GIM06', 'gstr2_return_period': 'GGM03', 'inv_itc_elgibity': 'GIM07', 'sale_through_ecommerce_operator': 'GGM04','invoice/note number': 'GDM01', 'invoice/note date': 'GDM02'}

error_constant_valid = {'document_number': 'GDV01', 'document_date': 'GDV02', 'original_document_number': 'GOV01',
                        'original_document_date': 'GOV02','original_month': 'GOV03',
                        'ref_document_number': 'GRV01', 'ref_document_date': 'GRV02', 'supply_type': 'GSV01',
                        'invoice_status': 'GIV01', 'invoice_category': 'GIV02',
                        'invoice_type': 'GIV03', 'total_invoice_value': 'GTV01', 'total_taxable_value': 'GTV02',
                        'txpd_taxtable_value': 'GTV03',
                        'shipping_bill_number': 'GSV02', 'shipping_bill_date': 'GSV03', 'reason': 'GRV03',
                        'port_code': 'GPV01',
                        'location': 'GLV01', 'gstr1_return_period': 'GGV01', 'gstr3b_return_period': 'GGV02',
                        'reverse_charge': 'GRV04','issez': 'GRV04',
                        'isamended': 'GIV04', 'amended_pos': 'GAV05', 'amended_period': 'GAV06',
                        'place_of_supply': 'GPV02',
                        'supplier_gstin': 'GSV04', 'buyer_gstin': 'GBV01', 'customer_name': 'GCV01',
                        'itemList': 'GIV05',
                        'igst_amount': 'GIVI01', 'cgst_amount': 'GIVC01', 'sgst_amount': 'GIVS01',
                        'taxable_value': 'GIVT01',
                        'hsn_code': 'GIVH01', 'product_name': 'GIVP01', 'item_description': 'GIVI02',
                        'quantity': 'GIVQ01',
                        'cess_amount': 'GIVC02', 'gst_rate': 'GIVG01', 'unit_of_product': 'GIVU01',
                        'itc_elgibity': 'GIV06', 'gstr2_return_period': 'GGV03', 'inv_itc_elgibity': 'GIV07', 'validate_gstin_for_buy_sup': 'GSV05', 'invoice_date_return_period': 'GGV04', '3b_auto_fill_period': 'GGV05', 'sale_through_ecommerce_operator': 'GGV06', 'etin': 'GGV07', 'ERP_document_number': 'GDV03', 'ERP_document_date': 'GDV04','invoice/note number': 'GDM01', 'invoice/note date': 'GDM02'}
full_form_supply_type = {
    "nor": "normal", "emp": "exempted", "nrt": "nil-rated", "ngs": "non-gst", "ngt": "non-gst"
}

gstr2_validationoff_fields = [
    {
        'name': 'supplier_gstin',
        'mandate': False,
        'extra_check': True,
        'checks': [{'method': 'check_for_supplier_gstin', 'kwargs': {},
                    'message': "should be of valid type."}]
    },
    {
        'name': 'sez_gstin',
        'mandate': False,
        'extra_check': True,
        'checks': [{'method': 'check_for_sez_gstin', 'kwargs': {},
                    'message': "Sez Gstin is Mandatory if Is Sez is Y"}]
    },
    {
        'name': 'port_code',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'str'}}]
    },
    {
        'name': 'txpd_taxtable_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'}}]
    },
    {
        'name': 'inv_itc_elgibity',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'yes', 'n', 'ip', 'is', 'cp', 'no']}}]
    },

    {
        'name': 'buyer_gstin',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
    {
        'name': 'supply_type',
        'mandate': True,
        'checks': [{'method': 'valid_in',
                    'kwargs': {'list_to_be_checked': ["nor", "emp", "nrt", "ngt"],'error_message': ["Normal", 'Exempted', 'Nil-Rated', 'Non-Gst'], "default_value": "nor"},
                    } ]
    },
    {
        'name': 'document_number',
        'mandate': True,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16},'message': "Invoice no/Note no/Bill of entry no. should not exceed 16 characters"},{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number2'}}]
    },
    {
        'name': 'document_date',
        'mandate': True,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {},
                    'message': 'Invoice date should not be future date / invalid date ( format dd-mm-yyyy or dd/mm/yyyy)'}]
    },
    # {
    #     'name': 'ERP_document_number',
    #     'mandate': False,
    #     'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number'}},
    #                {'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}}]
    # },
    {
        'name': 'ERP_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}},
                   {'method': 'future_date_check', 'kwargs': {}}]
    },
    {
        'name': 'isamended',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'issez',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'reverse_charge',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    {
        'name': 'payment_status',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n', 'P', 'p'], 'default_value': ''}}]
    },
    {
        'name': 'paid_amount',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float', 'default_value': 0.0}}]
    },
    {
        'name': 'place_of_supply',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_state_code}}]
    },
    {
        'name': 'invoice_category',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {
            'list_to_be_checked': ["txn", "cdn", "ddn", "imp", "vch", "isd"]}}]
    },

    {
        'name': 'invoice_status',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["add", "d"], 'default_value': "add"}}]
    },

    {
        'name': 'total_invoice_value',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'shipping_bill_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'shipping_bill_number',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number2'}},
                   {'method': 'check_len', 'kwargs': {'min_len': 3, 'max_len': 7}}]
    },
    {
        'name': 'amended_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': 'original_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number2'}}]
    },
    {
        'name': 'original_document_date',
        'mandate': False,
        'checks': [{'method': 'validate_invoice_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_date',
        'mandate': False,
        'checks': [{'method': 'valid_date', 'kwargs': {}}]
    },
    {
        'name': 'ref_document_number',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 0, 'max_len': 16}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'invoice_number2'}}]
    },
    {
        'name': 'gstr3b_return_period',
        'mandate': False,
        'checks': [{'method': 'validate_period', 'kwargs': {}}]
    },
    {
        'name': '3b_auto_fill_period',
        'mandate': False,
        'checks': [{'method': 'gstr3b_validate_period', 'kwargs': {},
                    'message': ' should be of valid type / format(mm-yyyy / mmyyyy)'}]
    },
    {
        'name': 'gstr2_return_period',
        'mandate': False,
        'checks': [{'method': 'gstr_validate_period', 'kwargs': {},
                   'message': ' should be of valid format(mm-yyyy)'}]
    },
    {
        'name': 'isamended',
        'mandate': False,
        'checks': [{'method': 'validate_dependency_check',
                    'kwargs':
                        {'field_to_be_present':
                             [
                                 # {'field_name': 'amended_period', 'checks': []},
                              {'field_name': 'original_document_number', 'checks': []},
                              {'field_name': 'original_document_date', 'checks': []}],
                         'field_name': 'isamended', 'field_value': 'y'}}]
    },
    {
        'name': 'gstr7_return_period',
        'mandate': False,
        'checks': [{'method': 'gstr_validate_period', 'kwargs': {},
                   'message': ' should be of valid format(mm-yyyy)'},
                   {'method': 'past_return_period_check', 'kwargs': {},
                   'message': 'should be valid month and year and should not be past months and years'}]
    },
    {
        'name': 'gstr7_amend_type',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ["rejected by deductee", "uploaded by deductor"]}}]
    },
    {
        'name': 'original_gstin_of_supplier',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}]
    },
]

gstr2_validationoff_inner_fields= [
    {
        'name': 'cess_amount',
        'mandate': False,
        'checks':  [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'sgst_amount',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'cgst_amount',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'igst_amount',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'quantity',
        'mandate': True,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'quantity'}}]
    },
    {
        'name': 'gst_rate',
        'mandate': True,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'taxable_value',
        'mandate': True,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'assessable_value',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'itc_elgibity',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['n', 'N', 'is', 'IS', 'IN', 'in', 'cp', 'CP']}}]
    },
    {
        'name': 'igst_tds',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'cgst_tds',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'sgst_tds',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
    {
        'name': 'original_taxable_value',
        'mandate': False,
        'checks': [{'method': 'check_data_types', 'kwargs': {'data_type': 'float'}}]
    },
]


gstr1_import_settings_fields = {

    'buyer_gstin': {
        'name': 'buyer_gstin',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'supplier_gstin'}}],
    },
    'reverse_charge': {
        'name': 'reverse_charge',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    'place_of_supply': {
        'name': 'place_of_supply',
        'mandate': True,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_state_code}}]
    },
    'invoice_value': {
        'name': 'invoice_value',
        'mandate': False,
        'checks': [{'method': 'validate_regex', 'kwargs': {'field_name': 'total_invoice_value'},
                    'message': ' should be of valid type. Upto 2 decimal allowed'}]
    },
    'product_name': {
        'name': 'product_name',
        'mandate': False,
        'checks': []
    },
}

gstr2_import_settings_fields = {
    'supplier_gstin': {
        'name': 'supplier_gstin',
        'mandate': False,
        'checks': [{'method': 'check_for_supplier_gstin', 'kwargs': {},
                    'message': "should be of valid type."}]
    },
    'reverse_charge': {
        'name': 'reverse_charge',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': ['y', 'Y', 'N', 'n']}}]
    },
    'place_of_supply': {
        'name': 'place_of_supply',
        'mandate': False,
        'checks': [{'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_state_code}}]
    },
    'hsn_code': {
        'name': 'hsn_code',
        'mandate': False,
        'checks': [{'method': 'check_len', 'kwargs': {'min_len': 4, 'max_len': 8}},
                   {'method': 'validate_regex', 'kwargs': {'field_name': 'hsn_check'}}]
    },
    'unit_of_product': {
        'name': 'unit_of_product',
        'mandate': False,
        'checks': [
            {'method': 'valid_in', 'kwargs': {'list_to_be_checked': valid_uqc_code}}]
    },
    'product_name': {
        'name': 'product_name',
        'mandate': False,
        'checks': []
    },
}