// un-minified version of the bookmarklet
javascript: (function() {
    function copyJsonToClipboard(data)
	{
        let listener = (event) => {
            event.preventDefault();
            event.clipboardData.setData("text/plain", JSON.stringify(data));
        };
        document.addEventListener("copy", listener);
        document.execCommand("copy");
        document.removeEventListener("copy", listener);
    }

    const hash = window.location.hash;
	const BOOKMARK_VERSION = 2;
	
	if(
		(
			hash.startsWith("#party/index/") ||
			hash.startsWith("#party/expectancy_damage/index") ||
			hash.startsWith("#tower/party/index/") ||
			(hash.startsWith("#event/sequenceraid") && hash.includes("/party/index/"))
		) &&
		!hash.startsWith("#tower/party/expectancy_damage/index/")
	)
	{
		const DARK_OPUS_IDS = [
			"1040310600","1040310700","1040415000","1040415100","1040809400","1040809500","1040212500","1040212600","1040017000","1040017100","1040911000","1040911100",
			"1040310600_02","1040310700_02","1040415000_02","1040415100_02","1040809400_02","1040809500_02","1040212500_02","1040212600_02","1040017000_02","1040017100_02","1040911000_02","1040911100_02",
			"1040310600_03","1040310700_03","1040415000_03","1040415100_03","1040809400_03","1040809500_03","1040212500_03","1040212600_03","1040017000_03","1040017100_03","1040911000_03","1040911100_03"
		];
		const ULTIMA_IDS = [
			"1040011900","1040012000","1040012100","1040012200","1040012300","1040012400",
			"1040109700","1040109800","1040109900","1040110000","1040110100","1040110200",
			"1040208800","1040208900","1040209000","1040209100","1040209200","1040209300",
			"1040307800","1040307900","1040308000","1040308100","1040308200","1040308300",
			"1040410800","1040410900","1040411000","1040411100","1040411200","1040411300",
			"1040507400","1040507500","1040507600","1040507700","1040507800","1040507900",
			"1040608100","1040608200","1040608300","1040608400","1040608500","1040608600",
			"1040706900","1040707000","1040707100","1040707200","1040707300","1040707400",
			"1040807000","1040807100","1040807200","1040807300","1040807400","1040807500",
			"1040907500","1040907600","1040907700","1040907800","1040907900","1040908000"
		];
		const ORIGIN_DRACONIC_IDS = [
			"1040815900","1040316500","1040712800","1040422200","1040915600","1040516500"
		];
		const DESTRUCTION_IDS = [
			"1040028900","1040122300","1040220300","1040621200","1040714700","1040817900"
		];
		let obj = {
            ver: BOOKMARK_VERSION,
            lang: Game.lang,
            p: parseInt(Game.view.deck_model.attributes.deck.pc.job.master.id, 10),
            pcjs: Game.view.deck_model.attributes.deck.pc.param.image,
            ps: [],
            pce: Game.view.deck_model.attributes.deck.pc.param.attribute,
            c: [],
            ce: [],
            ci: [],
            cb: [Game.view.deck_model.attributes.deck.pc.skill.count],
            cst: [],
            cn: [],
            cl: [],
            cs: [],
            cp: [],
            cwr: [],
            cpl: Game.view.deck_model.attributes.deck.pc.shield_id,
            fpl: Game.view.deck_model.attributes.deck.pc.familiar_id,
            qs: null,
            cml: Game.view.deck_model.attributes.deck.pc.job.param.master_level,
            cbl: Game.view.deck_model.attributes.deck.pc.job.param.perfection_proof_level,
            s: [],
            sl: [],
            ss: [],
            se: [],
            sp: [],
            ssm: Game.view.deck_model.attributes.deck.pc.skin_summon_id,
            w: [],
			wkey: {},
            wsm: [Game.view.deck_model.attributes.deck.pc.skin_weapon_id, Game.view.deck_model.attributes.deck.pc.skin_weapon_id_2],
            wl: [],
            wsn: [],
            wll: [],
            wp: [],
            wakn: [],
            wax: [],
            waxi: [],
            waxt: [],
            watk: Game.view.deck_model.attributes.deck.pc.weapons_attack,
            whp: Game.view.deck_model.attributes.deck.pc.weapons_hp,
            satk: Game.view.deck_model.attributes.deck.pc.summons_attack,
            shp: Game.view.deck_model.attributes.deck.pc.summons_hp,
            est: [Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute, Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage, Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage],
            estx: [],
            mods: Game.view.deck_model.attributes.deck.pc.damage_info.effect_value_info,
            sps: (Game.view.deck_model.attributes.deck.pc.damage_info.summon_name ? Game.view.deck_model.attributes.deck.pc.damage_info.summon_name : null),
            spsid: (Game.view.expectancyDamageData ? (Game.view.expectancyDamageData.imageId ? Game.view.expectancyDamageData.imageId : null) : null)
		};
        let qid = JSON.stringify(Game.view.deck_model.attributes.deck.pc.quick_user_summon_id);
        if (qid != null) {
            for (const i in Game.view.deck_model.attributes.deck.pc.summons) {
                if (Game.view.deck_model.attributes.deck.pc.summons[i].param != null && Game.view.deck_model.attributes.deck.pc.summons[i].param.id == qid) {
                    obj.qs = parseInt(i) - 1;
                    break
                }
            }
        };
        try {
            for (let i = 0; i < 4 - Game.view.deck_model.attributes.deck.pc.set_action.length; i++) {
                obj.ps.push(null);
            }
            Object.values(Game.view.deck_model.attributes.deck.pc.set_action).forEach(e => {
                obj.ps.push(e.name ? e.name.trim() : null);
            })
        } catch (error) {
            obj.ps = [null, null, null, null]
        };
        if (window.location.hash.startsWith("#tower/party/index/")) {
            Object.values(Game.view.deck_model.attributes.deck.npc).forEach(x => {
                Object.values(x).forEach(e => {
                    obj.c.push(e.master ? parseInt(e.master.id, 10) : null);
                    obj.ce.push(e.master ? parseInt(e.master.attribute, 10) : null);
                    obj.ci.push(e.param ? e.param.image_id_3 : null);
                    obj.cb.push(e.param ? e.skill.count : null);
                    obj.cst.push(e.param ? e.param.style : 1);
                    obj.cl.push(e.param ? parseInt(e.param.level, 10) : null);
                    obj.cs.push(e.param ? parseInt(e.param.evolution, 10) : null);
                    obj.cp.push(e.param ? parseInt(e.param.quality, 10) : null);
                    obj.cwr.push(e.param ? e.param.has_npcaugment_constant : null);
                    obj.cn.push(e.master ? e.master.short_name : null);
                });
            });
        } else {
            Object.values(Game.view.deck_model.attributes.deck.npc).forEach(e => {
                obj.c.push(e.master ? parseInt(e.master.id, 10) : null);
                obj.ce.push(e.master ? parseInt(e.master.attribute, 10) : null);
                obj.ci.push(e.param ? e.param.image_id_3 : null);
                obj.cb.push(e.param ? e.skill.count : null);
                obj.cst.push(e.param ? e.param.style : 1);
                obj.cl.push(e.param ? parseInt(e.param.level, 10) : null);
                obj.cs.push(e.param ? parseInt(e.param.evolution, 10) : null);
                obj.cp.push(e.param ? parseInt(e.param.quality, 10) : null);
                obj.cwr.push(e.param ? e.param.has_npcaugment_constant : null);
                obj.cn.push(e.master ? e.master.short_name : null);
            });
        }
        Object.values(Game.view.deck_model.attributes.deck.pc.summons).forEach(e => {
            obj.s.push(e.master ? parseInt(e.master.id.slice(0, -3), 10) : null);
            obj.sl.push(e.param ? parseInt(e.param.level, 10) : null);
            obj.ss.push(e.param ? e.param.image_id : null);
            obj.se.push(e.param ? parseInt(e.param.evolution, 10) : null);
            obj.sp.push(e.param ? parseInt(e.param.quality, 10) : null);
        });
        Object.values(Game.view.deck_model.attributes.deck.pc.sub_summons).forEach(e => {
            obj.s.push(e.master ? parseInt(e.master.id.slice(0, -3), 10) : null);
            obj.sl.push(e.param ? parseInt(e.param.level, 10) : null);
            obj.ss.push(e.param ? e.param.image_id : null);
            obj.se.push(e.param ? parseInt(e.param.evolution, 10) : null);
            obj.sp.push(e.param ? parseInt(e.param.quality, 10) : null);
        });
        Object.values(Game.view.deck_model.attributes.deck.pc.weapons).forEach(e => {
            obj.w.push(e.master ? e.param.image_id : null);
            obj.wl.push(e.param ? parseInt(e.param.skill_level, 10) : null);
            obj.wsn.push(e.param ? [e.skill1 ? e.skill1.image : null, e.skill2 ? e.skill2.image : null, e.skill3 ? e.skill3.image : null] : null);
            obj.wll.push(e.param ? parseInt(e.param.level, 10) : null);
            obj.wp.push(e.param ? parseInt(e.param.quality, 10) : null);
            obj.wakn.push(e.param ? e.param.arousal : null);
            obj.waxt.push(e.param ? e.param.augment_image : null);
            obj.waxi.push(e.param ? e.param.augment_skill_icon_image : null);
            obj.wax.push(e.param ? e.param.augment_skill_info : null);
			if(e.master && e.param.image_id)
			{
				let wid = e.param.image_id.split("_")[0];
				if(DARK_OPUS_IDS.includes(wid) || ULTIMA_IDS.includes(wid) || DESTRUCTION_IDS.includes(wid))
				{
					obj.wkey[wid] = {};
					if(e.skill3)
						obj.wkey[wid].sk3 = e.skill3.name;
				}
				else if(ORIGIN_DRACONIC_IDS.includes(wid))
				{
					obj.wkey[wid] = {};
					if(e.skill2)
						obj.wkey[wid].sk2 = e.skill2.name;
				}
			}
        });
        Array.from(document.getElementsByClassName("txt-gauge-num")).forEach(x => {
            obj.estx.push([x.classList[1], x.textContent]);
        });
		copyJsonToClipboard(obj);
    } else if (
		hash.startsWith("#zenith/npc") ||
		hash.startsWith("#tower/zenith/npc") ||
		/^#event\/[a-zA-Z0-9]+\/zenith\/npc/.test(hash)
	) {
        let obj = {
            ver: BOOKMARK_VERSION,
            lang: Game.lang,
            id: parseInt(Game.view.npcId, 10),
            emp: Game.view.bonusListModel.attributes.bonus_list,
            ring: Game.view.npcaugmentData.param_data,
            awakening: null,
            awaktype: null,
            domain: [],
            saint: [],
            extra: []
        };
        try {
			let l = document.getElementsByClassName("prt-current-awakening-lv")[0].children;
			let n = l.length - 1;
			obj.awakening = 0;
			for(let i = 0; i <= n; ++i)
			{
				obj.awakening += parseInt(l[i].className[l[i].className.length - 1]) * Math.pow(10, n - i);
			}
            obj.awaktype = document.getElementsByClassName("prt-arousal-form-info")[0].children[1].textContent;
            let domains = document.getElementById("prt-domain-evoker-list").getElementsByClassName("prt-bonus-detail");
            for (let i = 0; i < domains.length; ++i) {
                obj.domain.push([domains[i].children[0].className, domains[i].children[1].textContent, domains[i].children[2] ? domains[i].children[2].textContent : null]);
            }
            if (document.getElementById("prt-shisei-wrapper").getElementsByClassName("prt-progress-gauge").length > 0) {
                let saints = document.getElementById("prt-shisei-wrapper").getElementsByClassName("prt-progress-gauge")[0].getElementsByClassName("ico-progress-gauge");
                for (let i = 0; i < saints.length; ++i) {
                    obj.saint.push([saints[i].className, null, null]);
                }
                saints = document.getElementById("prt-shisei-wrapper").getElementsByClassName("prt-bonus-detail");
                for (let i = 0; i < saints.length; ++i) {
                    obj.saint.push([saints[i].children[0].className, saints[i].children[1].textContent, saints[i].children[2] ? saints[i].children[2].textContent : null]);
                }
            }
            if (document.getElementsByClassName("cnt-extra-lb extra numbers").length > 0) {
                let extras = document.getElementsByClassName("cnt-extra-lb extra numbers")[0].getElementsByClassName("prt-bonus-detail");
                for (let i = 0; i < extras.length; ++i) {
                    obj.extra.push([extras[i].children[0].className, extras[i].children[1].textContent, extras[i].children[2] ? extras[i].children[2].textContent : null]);
                }
            }
        } catch (error) {};
		copyJsonToClipboard(obj);
    } else if (
		hash.startsWith("#list/detail_npc") ||
		hash.startsWith("#party/list/detail_npc") ||
		hash.startsWith("#party/top/detail_npc") ||
		hash.startsWith("#tower/list/detail_npc") ||
		hash.startsWith("#tower/party/top/detail_npc") ||
		/^#event\/[a-zA-Z0-9]+\/list\/detail_npc/.test(hash)
	) {
        let obj = {
            ver: BOOKMARK_VERSION,
            lang: Game.lang,
            id: parseInt(Game.view.npcId, 10),
            artifact: {}
        };
        try {
            let af = document.getElementsByClassName("artifact-body");
            if (af.length > 0) {
                let img = af[0].getElementsByClassName("img-icon-body")[0].src;
                let skills = [];
                let elems = af[0].getElementsByClassName("prt-artifact-skill-item");
                for (let i = 0; i < elems.length; ++i) {
                    skills.push({
                        lvl: elems[i].getElementsByClassName("artifact-skill-level")[0].textContent,
                        icon: elems[i].getElementsByClassName("artifact-skill-icon")[0].getElementsByTagName("img")[0].src,
                        desc: elems[i].getElementsByClassName("artifact-skill-desc")[0].textContent,
                        value: elems[i].getElementsByClassName("artifact-skill-value")[0].textContent
                    });
                }
                obj.artifact = {
                    img: img,
                    skills: skills
                };
            }
        } catch (error) {};
		copyJsonToClipboard(obj);
    } else {
        alert('Please go to a GBF Party, Character or EMP screen')
    }
})()