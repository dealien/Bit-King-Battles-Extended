// Start ws connection after document is loaded
$(document).ready(function() {	
	
	var color_damage;
	var color_healing;
	
	// Load last saved king on load and set the vitals and shield
	// Needed to inital load data if AnkhBot is already running
	if (typeof settings !== "undefined") {
		
		// Extract current king and overlay settings data from the settings
		// file to mimic what the websocket sends over to reuse functions
		var loadedData = {
			"BKBData" : {
				"ColHealth": settings.bkb_overlay_col_health,
				"ColShield": settings.bkb_overlay_col_shield,
				"ColDamage": settings.bkb_overlay_col_damage,
				"ColHealing": settings.bkb_overlay_col_healing,
				"ColPrimary": settings.bkb_overlay_col_primary,
				"ColSecondary": settings.bkb_overlay_col_secondary,
				"VolHealthNorm": settings.bkb_overlay_vol_health_norm,
				"VolHealthCrit": settings.bkb_overlay_vol_health_crit,
				"VolShieldNorm": settings.bkb_overlay_vol_shield_norm,
				"VolShieldCrit": settings.bkb_overlay_vol_shield_crit,
				"VolHealNorm": settings.bkb_overlay_vol_heal_norm,
				"VolHealCrit": settings.bkb_overlay_vol_heal_crit,
				"VolDeath": settings.bkb_overlay_vol_death
			},
			"CurrentKing": {
				"UserName": settings.bkb_current_name,
				"DisplayName": settings.bkb_current_display,
				"AvatarUri": settings.bkb_current_avataruri,
				"Health": settings.bkb_current_hp,
				"MaxHealth": settings.bkb_current_mhp,
				"HealthPercentage": settings.bkb_current_hp / settings.bkb_current_mhp * 100,
				"Shield": settings.bkb_current_shield,
				"MaxShield": settings.bkb_current_mshield,
				"ShieldPercentage": settings.bkb_current_shield / settings.bkb_current_mshield * 100,
			}
		}

		// Set overlay settings
		SetOverlaySettings(loadedData);
		
		// Animate king data
		$("#king").queue(function() {
			var self = this;
			AnimateReload(loadedData, function() {
				$(self).dequeue();
			});
		});
	}
  	
	// Connect if API_Key is inserted
	// Else show an error on the overlay
	if (typeof API_Key === "undefined") {
		$("body").html("No API Key found or load!<br>Rightclick on the Scoreboard script in AnkhBot and select \"Insert API Key\"");
		$("body").css({"font-size": "20px", "color": "#ff8080", "text-align": "center"});
	}
	else {
		connectWebsocket();
	}
	
});

// Connect to AnkhBot websocket
// Automatically tries to reconnect on
// disconnection by recalling this method
function connectWebsocket() {
	
	//-------------------------------------------
	//  Create WebSocket
	//-------------------------------------------
	var socket = new WebSocket("ws://127.0.0.1:3337/streamlabs");

	//-------------------------------------------
	//  Websocket Event: OnOpen
	//-------------------------------------------
	socket.onopen = function() {
		
		// AnkhBot Authentication Information
		var auth = {
			author: "Ocgineer",
			website: "http://www.twitch.tv/ocgineer",
			api_key: API_Key,
			events: [
				"EVENT_BKB_REFRESH",
				"EVENT_BKB_HEAL",
				"EVENT_BKB_DAMAGE",
				"EVENT_BKB_KILL",
			]
		};
		
		// Send authentication data to AnkhBot ws server
		socket.send(JSON.stringify(auth));
	};

	//-------------------------------------------
	//  Websocket Event: OnMessage
	//-------------------------------------------
	socket.onmessage = function (message) {	
		
		// Parse message
		var socketMessage = JSON.parse(message.data);
		
		// EVENT_BKB_REFRESH
		if (socketMessage.event == "EVENT_BKB_REFRESH") {
			// Set overlay settings
			SetOverlaySettings(JSON.parse(socketMessage.data));
			// Animate King data
			$("#king").queue(function() {
				var eventData = JSON.parse(socketMessage.data);
				console.log(eventData);
				var self = this;
				AnimateReload(eventData, function() {
					$(self).dequeue();
				});
			});			
		}
		
		// EVENT_BKB_HEAL
		if (socketMessage.event == "EVENT_BKB_HEAL") {
			$("#king").queue(function() {
				var eventData = JSON.parse(socketMessage.data);
				var self = this;
				AnimateHeal(eventData, function() {
					$(self).dequeue();
				});
			});
		}
		
		// EVENT_BKB_DAMAGE
		if (socketMessage.event == "EVENT_BKB_DAMAGE") {			
			$("#king").queue(function() {
				var eventData = JSON.parse(socketMessage.data);
				console.log(eventData);
				var self = this;
				// Animate shield damage when having shield
				if (eventData.BKBData.HasShield) {			
					AnimateDamageShield(eventData, function() {
						// Animate health damage when took health damage
						if (eventData.BKBData.HealthDamage > 0) {
							AnimateDamageHealth(eventData, function() {
								$(self).dequeue();
							});
						}
						else {
							$(self).dequeue();
						}
					});
				}
				// Animate health damage when not having shield
				else {
					AnimateDamageHealth(eventData, function() {
						$(self).dequeue();
					});
				}
			});
		}
		
		// EVENT_BKB_KILL
		if (socketMessage.event == "EVENT_BKB_KILL") {	
			$("#king").queue(function() {
				var eventData = JSON.parse(socketMessage.data);
				var self = this;
				if (eventData.BKBData.HasShield) {
					AnimateKillShield(eventData, function() {
						AnimateKill(eventData, function() {
							$(self).dequeue();
						});
					});
				}
				else {
					AnimateKill(eventData, function() {
						$(self).dequeue();
					});
				}
			});
		}

	};
	
	//-------------------------------------------
	//  Websocket Event: OnError
	//-------------------------------------------
	socket.onerror = function(error) {	
		console.log("Error: " + error);
	}	
	
	//-------------------------------------------
	//  Websocket Event: OnClose
	//-------------------------------------------
	socket.onclose = function() {
		// Clear socket to avoid multiple ws objects and EventHandlings
		socket = null;		
		// Try to reconnect every 5s 
		setTimeout(function(){connectWebsocket()}, 5000);						
	}    
};

//-------------------------------------------
// Overlay Settings
// Set overlay settings like colors and volume
//-------------------------------------------
function SetOverlaySettings(data) {
	// Set overlay color settings
	$("#king").css("background", data.BKBData.ColPrimary);
	$("#vitals").css("background", data.BKBData.ColSecondary);
	$(".health").css("background", data.BKBData.ColHealth);
	$(".shield").css("background", data.BKBData.ColShield);
	$(".damage").css("background", data.BKBData.ColDamage);
	$(".healing").css("background", data.BKBData.ColHealing);
	// Set overlay volume settings
	$("#audio_damage_health_normal").prop("volume", data.BKBData.VolHealthNorm);
	$("#audio_damage_health_critical").prop("volume", data.BKBData.VolHealthCrit);
	$("#audio_damage_shield_normal").prop("volume", data.BKBData.VolShieldNorm);
	$("#audio_damage_shield_critical").prop("volume", data.BKBData.VolShieldCrit);
	$("#audio_heal_normal").prop("volume", data.BKBData.VolHealNorm);
	$("#audio_heal_critical").prop("volume", data.BKBData.VolHealCrit);
	$("#audio_death").prop("volume", data.BKBData.VolDeath);
}

//-------------------------------------------
// Animation: Reload
// Quick animation used on load and reload
//-------------------------------------------
function AnimateReload(data, cb) {	
	// Fade out stats and name
	$(".shield-stats").fadeOut(500);
	$(".vitals-stats").fadeOut(500);
	$(".name").fadeOut(500, function() {
		// Set Data
		$(".maximum-health").html(data.CurrentKing.MaxHealth);
		$(".current-health").html(data.CurrentKing.Health);
		$(".durability").html(data.CurrentKing.Shield);
		// Set name and fade in
		$(".name").html(data.CurrentKing.DisplayName).fadeIn(500, function() {
			// Animate health and damage bar
			$(".health").animate({width: data.CurrentKing.HealthPercentage + "%"}, 500);				
			$(".damage").animate({width: data.CurrentKing.HealthPercentage + "%"}, 500);
			$(".healing").animate({width: data.CurrentKing.HealthPercentage + "%"}, 500);
			// There is a shield
			if (data.CurrentKing.Shield > 0) {
				// Shield icon
				$(".vitals-label").removeClass("mdi-heart mdi-heart-broken").addClass("mdi-shield-half-full");
				// Animate shield and show shield stats
				$(".shield").show().animate({width: data.CurrentKing.ShieldPercentage + "%"}, 500, function() {
					$(".shield-stats").fadeIn(500, function() {
						// callback on animation done
						cb && cb();
					});
				});
			}
			else {
				// Heart icon
				$(".vitals-label").removeClass("mdi-heart-broken mdi-shield-half-full").addClass("mdi-heart");
				// Animate shield and show health stats
				$(".shield").animate({width: data.CurrentKing.ShieldPercentage + "%"}, 500, function() {
					$(".shield").hide();
					$(".vitals-stats").fadeIn(500, function() {
						// callback on animation done
						cb && cb();
					});
				});
			}
		});
	});
}

//-------------------------------------------
// Animation: Heal
// Health and damage bar animation on heal
//-------------------------------------------
function AnimateHeal(data, cb) {
	// Play health hit audio
	if (data.BKBData.IsHealCrit)
		$("#audio_heal_critical").trigger("play");
	else
		$("#audio_heal_normal").trigger("play");
	// Animate health hit
	$(".healing").animate(
		{
			// Update current-health (heal) each step of the animation
			width: data.NewKing.HealthPercentage + "%"
		},
		{
			duration: 1000,
			step: function(now, fx) {
				$(".current-health").html(Math.round(now * data.NewKing.MaxHealth / 100));
			},
			complete: function() {
				$(".current-health").html(data.NewKing.Health);
				$(".health").animate({width: data.NewKing.HealthPercentage + "%"}, 500, function() {
					$(".damage").css("width", data.NewKing.HealthPercentage + "%");
					// callback on animation done
					cb && cb();
				});
			}
		}
	);
}

//-------------------------------------------
// Animation: Damage Shield
// Damage shield animation
//-------------------------------------------
function AnimateDamageShield(data, cb) {
	// Play shield hit audio
	if (data.BKBData.IsShieldCrit)
		$("#audio_damage_shield_critical").trigger("play");
	else
		$("#audio_damage_shield_normal").trigger("play");
	// Animate shield hit
	$(".shield").animate(
		{
			width: data.NewKing.ShieldPercentage + "%"
		},
		{
			duration: 1000,
			step: function(now, fx) {
				// Update shield durability each step of the animation
				$(".durability").html(Math.round(now * data.NewKing.MaxShield / 100));
			},
			complete: function() {
				$(".durability").html(data.NewKing.Shield);
				// is it broken, hide shield and animate life
				if (data.BKBData.IsShieldBreak) {
					$(".shield").hide();
					$(".shield-stats").fadeOut(500, function() {
						// Change icon to heart
						$(".vitals-label").removeClass("mdi-heart-broken mdi-shield-half-full").addClass("mdi-heart");
						// After vital stats faded in, animate normal damage without shield if needed
						$(".vitals-stats").fadeIn(500, function() {
							// callback on animation done
							cb && cb();
						});
					});
				}
				else {
					// callback on animation done
					cb && cb();
				}
			}
		}
	);
}

//-------------------------------------------
// Animation: Damage Health
// Damage health animation
//-------------------------------------------
function AnimateDamageHealth(data, cb) {
	// Play health hit audio
	if (data.BKBData.IsHealthCrit)
		$("#audio_damage_health_critical").trigger("play");
	else
		$("#audio_damage_health_normal").trigger("play");
	// Animate health hit
	$(".healing").css("width", data.NewKing.HealthPercentage + "%");
	$(".health").animate(
	{
		width: data.NewKing.HealthPercentage + "%"
	},
	{
		duration: 1000,
		step: function(now, fx) {
			// Update current-health (drain) each step of the animation
			$(".current-health").html(Math.round(now * data.NewKing.MaxHealth / 100));
		},
		complete: function() {
			$(".current-health").html(data.NewKing.Health);
			$(".damage").animate({width: data.NewKing.HealthPercentage + "%"}, 500, function() {
				
				// callback on animation done
				cb && cb();
			});	
		}
	});
}

//-------------------------------------------
// Animation: Kill Shielded
// Kill animation breaking the shield first
//-------------------------------------------
function AnimateKillShield(data, cb) {
	// Play Critical shield hit audio
	$("#audio_damage_shield_critical").trigger("play");
	// Animate shield hit
	$(".shield").animate(
		{
			width: "0%"
		},
		{
			duration: 1000,
			step: function(now, fx) {
				// Update shield durability each step of the animation
				$(".durability").html(Math.round(now * data.CurrentKing.MaxShield / 100));
			},
			complete: function() {
				$(".durability").html(data.CurrentKing.Shield);
				// is it broken, hide shield and animate life
				$(".shield").hide();
				$(".shield-stats").fadeOut(500, function() {
					// Change icon to heart
					$(".vitals-label").removeClass("mdi-heart-broken mdi-shield-half-full").addClass("mdi-heart");
					// After vital stats faded in, animate normal damage without shield if needed
					$(".vitals-stats").fadeIn(500, function() {
						// callback on animation done
						cb && cb();
					});
				});
			}
		}
	);
}

//-------------------------------------------
// Animation: Kill
// Kill animation and king swap on kill
//-------------------------------------------
function AnimateKill(data, cb) {
	// Play critical health hit audio
	$("#audio_damage_health_critical").trigger("play");
	// Animate death
	$(".healing").css("width", "0%");
	$(".health").animate(
		{
			width: "0%"
		},
		{
			duration: 1000,
			step: function(now, fx) {
				// Update current-health (drain) each step of the animation
				$(".current-health").html(Math.round(now * data.CurrentKing.MaxHealth / 100));
			},
			complete: function() {
				// Play death audio
				$("#audio_death").trigger("play");
				// Change icon to broken heart after health bar is depleted
				$(".vitals-label").removeClass("mdi-heart mdi-shield-half-full").addClass("mdi-heart-broken");
				// Animate damage bar
				$(".damage").animate({width: "0%"}, 500, function() {
					// Fade out name and vitals stats
					$(".name").fadeOut(500);
					$(".vitals-stats").fadeOut(500, function() {
						// Set new data
						$(".maximum-health").html(data.NewKing.MaxHealth);
						$(".name").html(data.NewKing.DisplayName).fadeIn(500);
						$(".vitals-stats").fadeIn(500, function() {
							// Change icon to heart just before damage bar animates
							$(".vitals-label").removeClass("mdi-heart-broken mdi-shield-half-full").addClass("mdi-heart");
							// Animate 'damage' bar as healing
							$(".healing").animate(
								{
									width: data.NewKing.HealthPercentage + "%"
								},
								{
									duration: 1000,
									step: function(now, fx) {
										// Update current-health (refill) each step of the animation
										$(".current-health").html(Math.round(now * data.NewKing.MaxHealth / 100));
									},
									complete: function() {
										// Fix current health by actual data
										$(".current-health").html(data.NewKing.Health);
										// Animate the health bar
										$(".health").animate({width: data.NewKing.HealthPercentage + "%"}, 500, function() {
											$(".damage").css("width", data.NewKing.HealthPercentage + "%");
											// New King has shield
											if (data.NewKing.Shield > 0) {
												$(".vitals-stats").fadeOut(500, function() {
													$(".durability").html("0");
													$(".shield-stats").fadeIn(500, function() {
														$(".vitals-label").removeClass("mdi-heart-broken mdi-heart").addClass("mdi-shield-half-full");
														$(".shield").show().animate(
															{
																width: data.NewKing.ShieldPercentage + "%"
															},
															{
																duration: 1000,
																step: function(now, fx) {
																	$(".durability").html(Math.round(now * data.NewKing.MaxShield / 100));
																},
																complete: function() {
																	// callback on animation done
																	cb && cb();
																}
															}
														);
													});
												});
											}
											else {
												// callback on animation done
												cb && cb();
											}
										});
									}
								}
							);
						});
					}); 
				});
			}
		}
	); 
}