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

    let hash = window.location.hash;
	
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
		let obj = {
            ver: 1,
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
            ver: 1,
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
            obj.awakening = document.getElementsByClassName("prt-current-awakening-lv")[0].firstChild.className;
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
            ver: 1,
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
}())