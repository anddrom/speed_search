$(function() {
  var $searchForm = $('#searchForm');
  var $marketSearchForm = $('#marketSearchForm');
  var $resultsTree = $('#resultsTree');
  var $filterGroup = $('#filterGroup');

  var $filterDate = $('#filterDate');
  var $filterSort = $('#filterSort');

  var $selectState = $('#state');
  var $selectLocation = $('#location');

  var filterDate = 'all';
  var filterSort = 'coupon_lastseen';

  var results = [];

  var $searchLoader = $('#searchLoader');
  var $searchFormLoader = $('#searchFormLoader');

  // Default Search Ajax

  $searchForm.submit( function( event ) {
    event.preventDefault();
    event.stopPropagation();

    var form = event.target;

    if ( !form['location'].value ) {
      return false;
    }

    var payload = {
      state: form['state'].value,
      location: form['location'].value,
      competitor: form['competitor'].value,
    }

    $searchLoader.show();
    $filterGroup.hide();

    $.ajax({
      url: "/search",
      method: 'POST',
      data: payload,
      success: function (response) {
        if ( response.success ) {
          results = response.data;
          arrangeTree(results);

          $filterGroup.show();
        }

        $searchLoader.hide();
      },
      error: function (error) {
        console.error(error);
        $searchLoader.hide();
        $filterGroup.hide();
      }
    });
  });

  // Market Search Ajax

  $marketSearchForm.submit( function( event ) {
    event.preventDefault();
    event.stopPropagation();

    var form = event.target;
    var payload = {
      market: form['market'].value,
    }

    $searchLoader.show();
    $filterGroup.hide();

    $.ajax({
      url: "/market_search",
      method: 'POST',
      data: payload,
      success: function (response) {
        if ( response.success ) {
          results = response.data;
          arrangeTree(results);

          $filterGroup.show();
        }

        $searchLoader.hide();
      },
      error: function (error) {
        console.error(error);
        $searchLoader.hide();
        $filterGroup.hide();
      }
    });
  });

  function arrangeTree (jsons) {
    var treeData = {};

    // parse filter value
    var _filterDate = '1000';
    if ( filterDate != 'all' ) {
      dateAttrs = filterDate.split('_');
      var newDate =  new Date();
      if ( dateAttrs[1] == 'm' ) {
        newDate.setMonth(newDate.getMonth() - dateAttrs[0]);
        _filterDate = newDate.toISOString();
      } else if ( dateAttrs[1] == 'd' ) {
        newDate.setDate(newDate.getDate() - dateAttrs[0]);
        _filterDate = newDate.toISOString();
      }
    }

    jsons.forEach(function (element) {
      if ( element.coupon_lastseen >= _filterDate ) {
        var branch = treeData[element.coupon_category] || {};
        var subBranch = branch[element.coupon_type] || [];
        subBranch.push({
          coupon_text: element.coupon_text,
          coupon_lastseen: element.coupon_lastseen,
          note: element.note,
        });
        branch[element.coupon_type] = subBranch;
        treeData[element.coupon_category] = branch;
      }
    });

    var treeList = [];
    Object.keys(treeData).forEach(function (branchKey) {
      var branchData = treeData[branchKey];
      var branchList = {
        'text' : branchKey,
        'children': []
      };

      Object.keys(branchData).forEach(function (subBranchKey) {
        var subBranchData = branchData[subBranchKey];
        subBranchData.sort(function (a, b) {
          return a[filterSort] > b[filterSort] ? -1 : 1;
        })

        var subBranchList = {
          'text': subBranchKey,
          'children': subBranchData.map(function(sb) {
            return {
              'text': sb.note,
              'icon': 'jstree-file'
            }
          })
        };

        branchList.children.push(subBranchList);
      })

      treeList.push(branchList);
    })

    treeList.sort(function (a, b) {
      return a.text > b.text ? 1 : -1;
    })

    $resultsTree.data('jstree', false).empty().jstree({ 'core': { 'data': treeList } });
    // $resultsTree.jstree(true).refresh();
  }

  $filterDate.on('change', function(event) {
    filterDate = event.target.value;
    arrangeTree(results);
  })

  $filterSort.on('change', function(event) {
    filterSort = event.target.value;
    arrangeTree(results);
  })

  $selectState.on('change', function(event) {
    $selectLocation.html('');

    selectedState = event.target.value;
    if ( selectedState ) {
      var payload = {
        state: selectedState,
      }

      $searchFormLoader.show();
      $filterGroup.hide();

      $.ajax({
        url: "/location_search",
        method: 'POST',
        data: payload,
        success: function (response) {
          if ( response.success ) {
            var locations = response.data;
            locations.forEach(function (loc) {
              $selectLocation.append(`<option value="${loc}">${loc}</option>`);
            })
          }

          $searchFormLoader.hide();
        },
        error: function (error) {
          console.error(error);
          $searchFormLoader.hide();
        }
      });
    }
  })

});
