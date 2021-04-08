"use strict";
var overallpath1;
var accessiblepath1;
var overallpath2;
var accessiblepath2;
var map;
var slopelyr;
/*Load a KML file containing a specific path and add to the map*/
function loadpath(layerfile, color = '#D41159', dash = "4,4") {
	var customLayer = L.geoJson( null, {
		style : function(feature) {
			return {color: color, dashArray: dash};
		}
	});
	return omnivore.kml( './paths/' + layerfile, null, customLayer).addTo(map);
}
	
/*Clear all current paths from the map*/
function clearPaths() {	
		if (map.hasLayer(overallpath1)) {map.removeLayer(overallpath1)};
		if (map.hasLayer(overallpath2)) {map.removeLayer(overallpath2)};
		if (map.hasLayer(accessiblepath1)) {map.removeLayer(accessiblepath1)};
		if (map.hasLayer(accessiblepath2)) {map.removeLayer(accessiblepath2)};
}
/*Show the currently selected paths on the map*/
function showroute(e) {
		clearPaths();
		var origin;
		var destination;
		var basename1;
		var basename2;
		var layerfile1;
		var layerfile2;
		var overall;
		var accessible;
		origin = $('#origin').val();
		destination = $('#destination').val();
		basename1 = origin + destination;
		basename2 = destination + origin;
		overall = $('#all').prop("checked");
		accessible = $('#accessible').prop("checked");
		if (overall) {
			layerfile1 = basename1 + '-all.kml';
			overallpath1 = loadpath(layerfile1);	   
			layerfile2 = basename2 + '-all.kml';
			overallpath2 = loadpath(layerfile2);	   			
		}
		if (accessible) {
			layerfile1 = basename1 + '-access.kml';
			accessiblepath1 = loadpath(layerfile1, '#1A85FF', "");
			layerfile2 = basename2 + '-access.kml';
			accessiblepath2 = loadpath(layerfile2, '#1A85FF', "");
		}
}

function toggleSlope(e) {
	if ($('#slope').prop("checked")) {
		slopelyr.addTo(map);
		$('#slopekey').show();
	} else {
		map.removeLayer(slopelyr);
		$('#slopekey').hide();
	}
}

function toggleControl(e) {
	$('#control').slideToggle();
}

function hideControl(e) {
	if ($('#hamburger').is(':visible') {
		$('#control').slideUp();
	}
}
$(document).ready(function(){
	$('#all').change(showroute);
	$('#accessible').change(showroute);
	$('#slope').change(toggleSlope);
	$('#hamburger').click(toggleControl);
	$('#map').click(hideControl);
	

	// Base layers
	//  .. OpenStreetMap
	var osm = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'});

	// Overlay orthomosaic layer (TMS)
	var lyr = L.tileLayer('orthomosaic/{z}/{x}/{y}.png', {tms: true, 
		opacity: 1, 
		attribution: "",
		maxZoom: 21
	});

	//Overlay slope layer (TMS)

	slopelyr = L.tileLayer('slope-tiles/{z}/{x}/{y}.png', {tms: true, 
		opacity: 1, 
		attribution: "",
		maxZoom: 21
	});

	// Map
	map = L.map('map', {
		center: [40.44253, -79.94333],
		opacity: 1,
		zoom: 17,
		minZoom: 0,
		maxZoom: 21,
		layers: [osm]
	});

	var basemaps = {"OpenStreetMap": osm}
	var overlaymaps = {"Layer": lyr}
	lyr.addTo(map);

	//Add building names
	L.geoPackageFeatureLayer([], {
		geoPackageUrl: './overlays/building_labels.gpkg',
		layerName: 'building_labels',
		pointToLayer: function (geoJsonPoint, latlng) {
			var tooltip;
			var nullIcon;
			var marker;
			tooltip = L.tooltip({
				permanent:true,
				direction: 'center',
			});
			nullIcon = L.icon({iconUrl: 'icons/accessible_without_automatic_door.png', iconSize: [1,1]})
			marker = L.marker(
				latlng, {
				opacity: 0,
				icon: nullIcon
			}).bindTooltip(tooltip);
			marker.setTooltipContent(geoJsonPoint.properties.name);
			return marker;
		}
	}).addTo(map);

	//Add building entrances
	L.geoPackageFeatureLayer([], {
	geoPackageUrl: './overlays/all_building_entrances.gpkg',
	layerName: 'building_entrances',
	pointToLayer: function (geoJsonPoint, latlng) {
			var iconpath;
			var icon;
			var marker;
			switch(geoJsonPoint.properties.entrance) {
				case 'accessible':
					iconpath = 'icons/accessible_without_automatic_door.png';
					break;
				case 'inaccessible':
					iconpath = 'icons/inaccessible.png';
					break;
				case 'automatic':				
					iconpath = 'icons/accessible_with_automatic_door.png';
					break;
				default:
				iconpath = 'icons/unknown.png';
			}
			icon = L.icon({
				iconUrl: iconpath,
				iconSize: [16, 16],	
				});
			marker = L.marker(latlng, {
				icon: icon
				}
			);
			return marker;
		}
	}).addTo(map);

	/*Hide labels when zoomed out*/
	var tooltipThreshold = 17;
	map.on('zoomend', function() {
	  if (map.getZoom() < tooltipThreshold) {
		  $(".leaflet-tooltip").css("display","none")
	  } else { 
		  $(".leaflet-tooltip").css("display","block")
	  }
	})
	
	showroute();
}
);
